# Handoff — robo-esp32-fala (14/11/2026, projeto criado)

## Objetivo
Robô de mesa quadrado, o menor possível, com ESP32, que só conversa por voz através de um servidor. Sem movimento.
Pedido do Nei, literal: "quero fazer uma solução simples usando ESP32 e ele apenas falando comigo através de uma
API, um robô o menor possível, quadrado, sem movimentação".

## O que NÃO fazer
- Não usar API externa (OpenAI, Groq, ElevenLabs, Edge TTS, nuvem em geral) sem autorização explícita do Nei.
- Não usar a API da Anthropic: Claude só por `claude -p` pela assinatura, nunca com `--bare`.
- Não chamar `/api/jobs/tts` do inemavox sem `engine` nem usar `chatterbox-vc`: os dois caem no Edge (online).
- Não criar o repo no GitHub nem dar push: o Nei ainda não mandou.
- Não instalar PlatformIO, ESP-IDF nem modelo local novo.
- Não editar `~/projetos/robos-impressos` daqui (há uma sessão viva lá). Só ler e copiar do commit `aef010a`.
- Não apagar nada em `~/projetos/inemavox/jobs/`.

## Decisões tomadas (padrão; o Nei pode trocar)
| Assunto | Decisão |
|---|---|
| Placa | Seeed Studio XIAO ESP32S3, sem "Sense" (21 × 17,8 mm, 8 MB PSRAM) |
| Som | Microfone INMP441 (I²S), amplificador MAX98357A (I²S), falante de 28 mm 8 Ω |
| Ativação | Botão de apertar e segurar. Palavra de ativação fica para depois |
| Energia | USB-C, sempre no cabo. Sem bateria na fase 1 |
| Servidor | Local: Whisper do inemavox → `claude -p --model haiku` sem ferramentas → Chatterbox do inemavox |
| Voz | `rachel` (padrão da regra global) |
| Protocolo | `POST /v1/fala` com WAV 16 kHz mono 16 bits; resposta em WAV igual; token em `X-Robo-Token`; porta 8770 |
| Firmware | Arduino core `esp32:esp32` 3.3.12 pelo `arduino-cli` (já instalado), FQBN `esp32:esp32:XIAO_ESP32S3:PSRAM=opi` |
| Tamanho | Cubo de 40 mm (mínimo calculado 37,0 mm). 46 mm com bateria, 50 mm com falante de 40 mm |

## Feito (commit inicial, local)
- `DEFINICAO.md`, `LISTA-DE-COMPRAS.md`, `PLANO.md`, `README.md`, `CLAUDE.md`, `FALHAS.md`.
- `cad/parametros.py` + `cad/caixa_minima.py`: a conta do cubo roda (`python3 cad/caixa_minima.py`).
- `firmware/robo_fala/robo_fala.ino`: esqueleto que compila (277 587 bytes) e confere a PSRAM.
- `servidor/README.md` com a receita da F1 e `servidor/env.exemplo`.
- Testado: `claude -p --model haiku --tools "" --strict-mcp-config --no-session-persistence` respondeu em 5,0 s
  pela assinatura. A API do inemavox (`127.0.0.1:8010`) respondeu `ok`, versão 1.15.4.

## Não verificado
- Nenhuma transcrição nem voz foi gerada: o tempo total de uma resposta é desconhecido.
- Nenhuma peça comprada nem medida. Preços são estimativa, não lidos em loja. Compra da XIAO no Brasil não conferida.
- A pinagem (DEFINICAO.md, seção 9) é proposta. O cubo de 40 mm é conta de empilhamento, sem modelo 3D.

## Fica com o Nei
1. Comprar os itens 1 a 7 da `LISTA-DE-COMPRAS.md` (R$ 158–370, estimativa).
2. Confirmar a voz (`rachel`) ou escolher outra.
3. Dizer se prefere o atalho pronto M5Stack Atom Echo (cubo de 24 mm, sem solda; DEFINICAO.md, seção 5).

## Próxima ação exata
**Fase F1 do `PLANO.md`: escrever o servidor local. Não precisa de nenhuma peça.**
1. `cp servidor/env.exemplo servidor/.env` e trocar o `ROBO_TOKEN`.
2. Criar `servidor/teste/pergunta.wav` sem esperar o Nei: gerar "que horas são em Tóquio?" pela rota
   `/api/jobs/tts/upload` do inemavox (voz `rachel`) e converter com `ffmpeg -ar 16000 -ac 1 -c:a pcm_s16le`.
   Esse passo já prova a etapa de voz. Uma gravação da voz do Nei entra depois, como segundo teste.
3. Escrever `servidor/servidor.py` (só biblioteca padrão) seguindo "Receita de um turno" do `servidor/README.md`.
4. Escrever `servidor/testar.py` com os 8 critérios da F1.
5. Rodar até `python3 servidor/testar.py servidor/teste/pergunta.wav` terminar em `PASSOU` três vezes seguidas e
   gravar os tempos em `servidor/MEDIDAS.md`. Commit.
6. Se o total passar de 20 s, parar e levar os números ao Nei antes da F2.

Por quê primeiro a F1: é a única fase sem hardware, e a demora da resposta é o maior risco do projeto.

## Contexto extra
- A pasta ainda não é uma execução longa. Se a F1 virar trabalho de horas:
  `~/projetos/execucao-longa/tools/novo-longrun.sh robo-esp32-fala f1-servidor`.
- No fim de uma rodada: avisar o Nei com `~/projetos/wifi/scripts/avisa-v3.sh "<msg>"`.
