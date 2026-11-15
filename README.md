# robo-esp32-fala

Um cubo de mesa de 40 mm com um ESP32 dentro. Você aperta o botão, fala, e ele responde com voz.
Não anda, não gira, não tem motor. Quem entende a fala, escreve a resposta e gera a voz é um servidor local na sua
máquina, sem API externa.

**Estado em 14/11/2026: só a definição.** Nada foi comprado, soldado nem impresso. O servidor ainda não foi escrito.
O firmware é um esqueleto que pisca o LED.

| Para | Onde |
|---|---|
| Entender o que é e o que foi decidido | [DEFINICAO.md](DEFINICAO.md) |
| Comprar | [LISTA-DE-COMPRAS.md](LISTA-DE-COMPRAS.md) |
| Ver as fases e o critério de pronto de cada uma | [PLANO.md](PLANO.md) |
| Servidor local (transcrição, resposta, voz) | [servidor/README.md](servidor/README.md) |
| Programa do ESP32 | [firmware/README.md](firmware/README.md) |
| Caixa impressa | [cad/README.md](cad/README.md) |
| Retomar o trabalho | [handoffs/latest.md](handoffs/latest.md) |

## Em números

- Cubo: 40 mm de lado (mínimo calculado: 37,0 mm). Com bateria: 46 mm. Com falante de 40 mm: 50 mm.
- Placa: Seeed Studio XIAO ESP32S3, 21 × 17,8 mm, 8 MB de PSRAM.
- Peças da fase 1: R$ 158–370 (estimativa, não conferida em loja).
- Áudio: 16 kHz, 16 bits, mono, nos dois sentidos. Fala de até 15 s.
- Impressora: Bambu Lab A1. Cerca de 22 g de PLA (estimativa por volume).

## Como funciona

1. Você segura o botão e fala. O ESP32 grava.
2. Você solta. O ESP32 manda o WAV por Wi-Fi para o servidor (`POST /v1/fala`).
3. O servidor transcreve com o Whisper local, pede a resposta ao `claude -p` e gera a voz com o Chatterbox local.
4. O ESP32 toca a resposta.

## O processo, do início ao fim

Legenda: 🧠 sessão com o Nei · ⚙️ comando/script · 🤖 `claude -p`

| # | Passo | Comando | Quem | Existe hoje? |
|---|---|---|---|---|
| 1 | Ler a definição e confirmar placa, voz e tamanho | [DEFINICAO.md](DEFINICAO.md), seção 3 | 🧠 | sim |
| 2 | Comprar as peças | [LISTA-DE-COMPRAS.md](LISTA-DE-COMPRAS.md) | 🧠 | sim |
| 3 | Medir as peças marcadas NC e corrigir as medidas | editar `cad/parametros.py` | 🧠 | sim |
| 4 | Recalcular o tamanho do cubo | `python3 cad/caixa_minima.py` | ⚙️ | sim |
| 5 | Copiar o `.env` do servidor e escolher o token | `cp servidor/env.exemplo servidor/.env` | 🧠 | sim |
| 6 | Subir o servidor do robô | `python3 servidor/servidor.py` | ⚙️ | não: fase F1 |
| 7 | Testar o servidor com um WAV, sem o robô | `python3 servidor/testar.py servidor/teste/pergunta.wav` | ⚙️ | não: fase F1 |
| 8 | Dentro de cada turno: escrever a resposta | `claude -p --model haiku --tools "" --strict-mcp-config --no-session-persistence …` | 🤖 | comando testado |
| 9 | Soldar microfone, botão, amplificador e falante na placa | [DEFINICAO.md](DEFINICAO.md), seção 9 | 🧠 | — |
| 10 | Preencher Wi-Fi, endereço do servidor e token | `cp firmware/robo_fala/segredos.exemplo.h firmware/robo_fala/segredos.h` | 🧠 | sim |
| 11 | Compilar o firmware | `arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi firmware/robo_fala` | ⚙️ | sim (esqueleto) |
| 12 | Gravar na placa | `arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi -p /dev/ttyACM0 firmware/robo_fala` | ⚙️ | não testado: sem placa |
| 13 | Conversar na bancada: 5 perguntas seguidas | [PLANO.md](PLANO.md), fases F2 e F3 | 🧠 | — |
| 14 | Gerar e verificar a caixa (11 testes) | pipeline do `robos-impressos`, receita em [cad/README.md](cad/README.md) | ⚙️ | não: fase F4 |
| 15 | Imprimir a peça de teste e depois a caixa | 3MF no fatiador da Bambu Lab A1 | 🧠 | — |
| 16 | Montar, fechar e repetir as 5 perguntas | [PLANO.md](PLANO.md), fase F4 | 🧠 | — |
| 17 | Guia e publicação | só com a ordem do Nei: [PLANO.md](PLANO.md), fase F5 | 🧠 | — |

O único passo com `claude -p` é o 8, e ele roda pela assinatura, sem ferramentas.

## Regras

- Nenhuma API externa sem autorização explícita do Nei. As opções de nuvem estão listadas na DEFINICAO.md, seção 10,
  e nenhuma está implementada.
- Claude só pela assinatura (`claude -p`), nunca por chave de API.
- Repo local por enquanto: sem remoto e sem push até o Nei mandar.

## Parente próximo

O pipeline de CAD e o estilo dos documentos vêm do [robos-impressos](https://github.com/inematds/robos-impressos),
o projeto dos robôs de 30 cm. Este aqui é separado e não depende daquele para rodar.
