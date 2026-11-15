# Handoff — robo-cores3-lite (15/11/2026, troca de placa e de nome)

## Objetivo
Robô de mesa quadrado, sem movimento, na placa pronta M5Stack CoreS3 Lite: conversa por voz, mostra rosto e
legenda, enxerga pela câmera. Duas opções de cérebro: B, servidor local (padrão), e A, direto numa API.

Ordens do Nei, literais (15/11/2026):
- "quero duas opções, uma solução falar direto com uma api, e a outra falar com um servidor. quero tela, mic e voz,
  uma opção a mais seria reconhecer imagem e vídeo"
- "sim, foca na lite e segue, então já muda o nome do projeto para focar nesta aqui"

## O que NÃO fazer
- Não chamar nenhuma API externa (Gemini, OpenAI, Groq, ElevenLabs, Edge) sem autorização explícita do Nei com
  serviço e finalidade. A opção A é só desenho.
- Não usar a API da Anthropic: Claude só por `claude -p` pela assinatura, nunca com `--bare`.
- Não liberar ferramentas no `claude -p` do robô para fazer a foto entrar sem perguntar ao Nei.
- Não chamar `/api/jobs/tts` do inemavox sem `engine` nem usar `chatterbox-vc` (caem no Edge, online).
- Não instalar M5Unified/M5GFX sem avisar o Nei. Não instalar PlatformIO, ESP-IDF nem modelo local novo.
- Não criar o repo no GitHub nem dar push.
- Não apagar nada em `~/projetos/inemavox/jobs/`.

## Decisões (15/11/2026)
| Assunto | Decisão |
|---|---|
| Placa | M5Stack CoreS3 Lite (tem câmera; a SE não tem). Waveshare 1,54" fica como variante futura só de voz |
| Nome | Projeto renomeado de `robo-esp32-fala` para `robo-cores3-lite` (pasta movida para `~/projetos/robo-cores3-lite`) |
| Ativação | Segurar o dedo na tela |
| Ordem | F1 (servidor, opção B) → F2 (placa na opção B) → F3 (opção A, se autorizada) → F4 (visão) |
| Firmware | FQBN `esp32:esp32:m5stack_cores3`; esqueleto compila (300 492 bytes, 9%) |
| Protocolo | `/v1/fala` (WAV) + `/v1/foto` (JPEG, guardado 60 s, ligado por `X-Turno`), porta 8770 |

Fatos verificados em 15/11: microfone e falante da CoreS3 dividem o barramento I²S (doc M5Stack): conversa meio a
meio, interromper só pelo toque. `esp_camera` vem no core instalado. M5Unified não cuida da câmera.

## Não verificado
- Preço em reais (AliExpress só mostra no navegador). Especificações da Lite vêm da CNX Software.
- A placa `m5stack_cores3` na Lite e o modo da PSRAM (padrão QSPI; se der 0, `PSRAM=opi`).
- Como mandar foto ao `claude -p` sem ferramentas (candidato: `--input-format stream-json` com bloco de imagem).
- Nenhuma transcrição nem voz gerada; tempo total da opção B desconhecido.

## Fica com o Nei
1. Comprar a CoreS3 Lite e dizer o preço em reais.
2. Confirmar a voz `rachel` ou escolher outra.
3. Opção A: qual API (Gemini Live, OpenAI Realtime) e variante A1 (direto) ou A2 (via servidor); autorização escrita.

## Próxima ação exata
**Fase F1 do `PLANO.md`: escrever o servidor local. Não precisa da placa.**
1. `cp servidor/env.exemplo servidor/.env` e trocar o `ROBO_TOKEN`.
2. Gerar `servidor/teste/pergunta.wav` ("que horas são em Tóquio?") pela rota `/api/jobs/tts/upload` do inemavox,
   voz `rachel`, e converter com `ffmpeg -ar 16000 -ac 1 -c:a pcm_s16le`. Idem `pergunta-visao.wav`
   ("o que você está vendo?") e uma `foto.jpg` 640 × 480.
3. Testar à parte como a foto entra no `claude -p` sem ferramentas, antes de escrever o servidor.
4. Escrever `servidor/servidor.py` (só biblioteca padrão) e `servidor/testar.py` com os 10 critérios da F1.
5. Rodar até três `PASSOU` seguidos; tempos em `servidor/MEDIDAS.md`. Commit.
6. Se o total passar de 20 s, parar e levar os números ao Nei antes da F2.
