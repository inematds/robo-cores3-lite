# PLANO — robô ESP32 que só fala

Cada fase tem um critério de pronto que se confere com um comando ou uma medida. Fase sem o critério cumprido não
está pronta. O que cada peça é e por que foi escolhida está na [DEFINICAO.md](DEFINICAO.md).

Ordem: a F1 não precisa de nenhuma peça e começa já. A F0 (compra) corre em paralelo. F2 e F3 precisam das peças.
A F4 pode ser desenhada antes, mas só imprime depois de medir as peças.

| Fase | O que entrega | Precisa de |
|---|---|---|
| F0 | Peças compradas e medidas | Nei |
| F1 | Servidor local responde a um WAV de teste | Nada: só a máquina |
| F2 | Firmware grava e envia | F0, F1 |
| F3 | Firmware toca a resposta: conversa completa na bancada | F2 |
| F4 | Caixa impressa e fechada | F0 (medidas), F3 |
| F5 | Guia e publicação | F4 e a ordem do Nei |
| F6 | Opcionais: olhos, bateria, palavra de ativação | Decisão do Nei, um por um |

## F0 — Compra e medidas

O que fazer: comprar os itens 1 a 7 da [LISTA-DE-COMPRAS.md](LISTA-DE-COMPRAS.md). Quando chegarem, medir com o
paquímetro tudo o que está marcado NC e corrigir `cad/parametros.py`.

Pronto quando:
- Em `cad/parametros.py`, estes campos trocaram o comentário NC por "medido em <data>": `FALANTE_28.altura`,
  `XIAO.altura`, `XIAO.usb_passa_da_borda`, `BOTAO.altura`, `MIC.diametro`, `MIC.espessura`, `AMP.placa` (do
  módulo que chegou), `ANTENA.tamanho` e `PLUGUE_USB_C`. Conferir: fora o cabeçalho e a `MARGEM_NC`,
  `grep -n "NC" cad/parametros.py` só mostra `FIOS`, o falante de 40 mm e a bateria.
- `python3 cad/caixa_minima.py` roda e o alvo da variante A continua em 40 mm. Se subir, registrar o novo número na
  DEFINICAO.md, seção 12, no mesmo commit.
- O lado do furo do som do INMP441 está anotado em `cad/parametros.py` (`furo_do_som`).

## F1 — Servidor local responde a um WAV de teste

O que fazer: escrever `servidor/servidor.py` (só biblioteca padrão do Python) e `servidor/testar.py`, conforme
[servidor/README.md](servidor/README.md). Criar `servidor/teste/pergunta.wav` sem depender de ninguém: gerar a frase
"que horas são em Tóquio?" pela rota `/api/jobs/tts/upload` do inemavox (voz `rachel`) e converter com
`ffmpeg -ar 16000 -ac 1 -c:a pcm_s16le`. Uma gravação da voz do Nei entra depois, como segundo teste.

Pronto quando, com o servidor no ar (`python3 servidor/servidor.py`):

| # | Comando | Saída esperada |
|---|---|---|
| 1 | `python3 servidor/testar.py servidor/teste/pergunta.wav` | Termina com `PASSOU` e código 0. Mostra `OUVIDO:`, `RESPOSTA:` e `TEMPOS:` |
| 2 | `ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -of csv=p=0 servidor/teste/resposta.wav` | `pcm_s16le,16000,1` |
| 3 | o `testar.py` mede o volume da resposta com `ffmpeg -af volumedetect` | Volume médio acima de −40 dB (o Chatterbox já gerou silêncio "com sucesso" no passado) |
| 4 | o `testar.py` transcreve a `resposta.wav` e compara com o texto de `X-Resposta` | 80% ou mais das palavras batem |
| 5 | `python3 servidor/testar.py --limites` | Token errado → 401. Corpo de 2 MB → 413. WAV de 3 s de silêncio → 204, pela trava de volume, sem chamar o Whisper. Arquivo que não é WAV → 415 |
| 6 | `grep -rnE "https?://" servidor/*.py \| grep -v 127.0.0.1` | Nada: o servidor só fala com a própria máquina |
| 7 | `grep -rn "api/jobs/tts\"" servidor/*.py` | Nada: só existe a rota `/api/jobs/tts/upload` (Chatterbox local) |
| 8 | rodar o comando 1 três vezes seguidas | `PASSOU` nas três; o `total` de cada uma fica gravado em `servidor/MEDIDAS.md` |

Meta de tempo: resposta de uma frase em até 20 s com os modelos já carregados. É meta, não medida: a F1 mede e
grava o número real. Se passar de 20 s, registrar onde o tempo foi gasto e levar ao Nei antes de seguir.

## F2 — Firmware grava e envia

O que fazer: soldar microfone e botão na XIAO (fios de 6 a 8 cm), ligar pelo USB e escrever a parte de gravação e
envio em `firmware/robo_fala/`, conforme [firmware/README.md](firmware/README.md).

Pronto quando:

| # | Comando ou ação | Saída esperada |
|---|---|---|
| 1 | `arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi firmware/robo_fala` | Código 0 |
| 2 | Gravar e abrir o monitor serial | Linha com `PSRAM:` maior que zero, Wi-Fi conectado e `GET /saude` → 200 |
| 3 | Segurar o botão 3 s e dizer "um, dois, três, testando" a 50 cm, três vezes | O log do servidor mostra `OUVIDO:` com a frase certa nas três |
| 4 | `ffprobe` na `pergunta.wav` que o servidor guardou | `pcm_s16le,16000,1`, duração entre 2,5 e 3,5 s |
| 5 | `ffmpeg -af volumedetect` na mesma gravação | Volume médio acima de −35 dB e pico abaixo de 0 dB (sem estourar) |
| 6 | Segurar o botão por 20 s | A gravação para sozinha em 15 s e é enviada; a placa não reinicia |
| 7 | Desligar o servidor e apertar o botão | LED de erro por 2 s e volta a "pronto"; a placa não reinicia |

## F3 — Toca a resposta

O que fazer: soldar o amplificador e o falante, escrever a parte que recebe o WAV e toca.

Pronto quando:

| # | Ação | Saída esperada |
|---|---|---|
| 1 | Cinco perguntas seguidas, sem reiniciar | Cinco respostas tocadas até o fim, sem estalo no começo nem corte no final |
| 2 | Ouvir a 1 m, numa sala comum | Dá para entender todas as palavras |
| 3 | Ler o monitor serial | Cada turno mostra o tempo do botão solto até o primeiro som; os cinco tempos vão para `servidor/MEDIDAS.md` |
| 4 | Apertar o botão durante a fala | A fala para e a gravação nova começa |
| 5 | Deixar ligado 30 min sem uso e fazer uma pergunta | Responde normalmente (o Wi-Fi reconecta sozinho se caiu) |
| 6 | Repetir os testes 6 e 7 da F2 | Continuam passando |

## F4 — Caixa impressa

O que fazer: trazer o pipeline de CAD do `robos-impressos` (receita em [cad/README.md](cad/README.md)), desenhar
`casca`, `base`, `berco` e `tecla`, e os envelopes dos componentes com as medidas da F0.

Pronto quando:

| # | Comando ou ação | Saída esperada |
|---|---|---|
| 1 | Gerar as peças (comando do pipeline) | STL e 3MF de cada peça, já na posição de impressão |
| 2 | Verificar (comando do pipeline) | "TUDO PASSOU" nos 11 testes, com os envelopes dos componentes dentro do teste de interferência |
| 3 | Medir no modelo | Lado do cubo de 40 mm (ou o número novo da F0); parede de 2,0 mm ou mais; nenhuma peça pede suporte |
| 4 | Imprimir a peça de teste (cupom) | O plugue USB-C entra até o fim pela abertura, o falante assenta no anel, o parafuso M2 pega, a tecla desce e volta |
| 5 | Imprimir e montar | A caixa fecha sem forçar fio nenhum; o cabo USB-C encaixa com a caixa fechada |
| 6 | Paquímetro no cubo montado | Lado dentro de ± 0,3 mm do projeto |
| 7 | Repetir o teste 1 da F3 com a caixa fechada | Cinco respostas, e o `OUVIDO:` continua certo com o microfone atrás do furo |

## F5 — Guia e publicação

Só com a ordem do Nei: criar o repo `inematds/robo-esp32-fala`, primeiro `git push`, guia em `guia/index.html`
(skill `projetos-landing-guia`, PT + `/en/` + `/es/`, tradução pelo `inema-traduz`), portal.

Pronto quando:
- O guia abre em `https://inematds.github.io/robo-esp32-fala/guia/` nos três idiomas.
- O revisor independente (modelo de `~/.claude/runbooks/revisor-independente.md`) deu nota e a nota está registrada.
- O README tem a seção "O processo, do início ao fim" batendo com o que foi feito de verdade.
- O push entrou no `origin`. O Vercel não é conferido.

## F6 — Opcionais (um por um, só com decisão do Nei)

| Opcional | Critério de pronto |
|---|---|
| Olhos (LED ou OLED) | Cada estado do firmware tem uma cor ou um desenho diferente, visível a 1 m |
| Bateria | Uma hora de uso fora do cabo, com uma pergunta a cada 5 min, e carga completa pelo USB-C |
| Palavra de ativação | 9 acertos em 10 tentativas a 1 m e nenhuma ativação falsa em 30 min de TV ligada |
| Opção de nuvem | Só depois de o Nei autorizar por escrito o serviço e a finalidade |

## Riscos

| Risco | O que pode acontecer | Como se descobre cedo | Saída |
|---|---|---|---|
| Demora da resposta | Whisper + `claude -p` + Chatterbox somam mais de 20 s e a conversa fica arrastada | F1, medida 8 | Daemon do Whisper na memória; resposta de uma frase; LED de "pensando"; levar o número ao Nei |
| GPU ocupada | Outro trabalho na GPU (render, narração) atrasa a voz ou a transcrição | F1, rodando com a máquina em uso normal | Fila `~/projetos/wifi/scripts/fila-vaga gpu`; resposta 503 com LED de erro em vez de travar |
| Voz muda | O Chatterbox já entregou silêncio como se fosse sucesso | F1, teste 3 | O teste de volume barra |
| Número lido errado | O Chatterbox lê "2026" como "2006" | F1, teste 4 | A persona manda escrever número e ano por extenso |
| Engine errada | Uma chamada de voz sem `engine` cai no Edge, serviço online | F1, teste 7 | Só a rota `/api/jobs/tts/upload` |
| Pastas de job acumulando | Cada fala cria uma pasta de transcrição e uma de voz em `~/projetos/inemavox/jobs/` e não há limpeza automática | F1, olhando o tamanho de `jobs/` depois de 20 turnos | Combinar com o Nei a limpeza; não apagar nada do inemavox por conta própria |
| Fala vira comando | Alguém fala algo que tenta fazer o `claude -p` agir na máquina | Revisão do comando na F1 | `--tools ""`, sem MCP, pasta vazia, sem sessão salva |
| Servidor aberto na rede | Outro aparelho da casa manda áudio para o servidor | F1, teste 5 | Token no cabeçalho; ouvir só no endereço da rede local |
| Medidas NC | Falante, placa ou botão mais altos que o reservado: o cubo de 40 mm não fecha | F0 | Recalcular; plano B de 45 mm |
| Antena sem lugar | A antena da XIAO não cabe numa parede interna de 36 mm | F0, medindo a antena | Dobrar no canto ou subir o cubo |
| Solda apertada | 12 fios num espaço de 36 mm: fio solto, curto | F3, com tudo fora da caixa | Berço que segura as placas; fios coloridos; testar antes de fechar |
| Eco e microfonia | O microfone ouve o falante | F3 | O robô não grava enquanto fala |
| Som fraco | Falante de 28 mm numa caixa pequena soa fino | F3, teste 2 | Subir o ganho do amplificador; falante de 40 mm (cubo de 50 mm) |
| Estalo ao tocar | O amplificador estala ao ligar e desligar o I²S | F3, teste 1 | Manter o I²S ligado mandando silêncio |
| Plugue USB-C não entra | A parede de 2 mm impede o plugue de chegar ao fundo | F4, teste 4 | Rebaixo para o corpo do plugue |
| Compra | XIAO ESP32S3 difícil de achar ou cara no Brasil | F0 | XIAO Sense ou ESP32-S3-Zero (seção 5 da DEFINICAO.md) |
