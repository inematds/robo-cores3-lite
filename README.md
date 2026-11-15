# robo-cores3-lite

[![Robô que conversa](guia/assets/banner.jpg)](https://inematds.github.io/robo-cores3-lite/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

🎬 Vídeo: https://www.youtube.com/watch?v=ckhcNbClXNs

## O que é

Este é um projeto aberto para montar um robô de mesa que conversa por voz: você segura o dedo na tela, fala, e ele
responde em voz alta, com o texto na tela, e pode olhar pela câmera. O corpo é uma placa pronta, a M5Stack CoreS3
Lite (um quadrado de 5 cm com tela, câmera, microfones e alto-falante, sem solda). O "cérebro" passa pelo seu
computador: ele transcreve e gera a voz ali mesmo e pede a resposta ao Claude pela sua assinatura, sem pagar por
pergunta. Hoje esse servidor está pronto e medido; a placa ainda não chegou,
então o robô inteiro ainda não foi testado.

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/robo-cores3-lite/guia/**

## Mais detalhes

Um robô de mesa quadrado, sem movimento, feito com a **M5Stack CoreS3 Lite**: ele ouve, responde com voz, mostra um
rosto e o texto na tela, e enxerga pela câmera. A placa já vem pronta, sem solda.

Duas opções de "cérebro":
- **Opção B (padrão): servidor local** nesta máquina. Whisper → `claude -p` pela assinatura → Chatterbox. Sem custo por pergunta (usa a assinatura do Claude).
- **Opção A: direto numa API** de voz em tempo real (Gemini Live ou OpenAI Realtime). Só desenho: nada é chamado sem
  autorização do Nei (Nei Maldaner, autor do projeto).

**Estado em 15/11/2026: servidor da opção B pronto (F1), placa ainda não chegou.** Com a resposta por partes, o
primeiro som sai em 6,8 a 7,6 s, e uma frase de espera ("deixa eu ver o relógio…") cobre o silêncio; 19 s na
primeira depois de 10 min parado; a foto também funciona. O firmware é um esqueleto
que compila e mostra a PSRAM.

| Para | Onde |
|---|---|
| Entender o que é e o que foi decidido | [DEFINICAO.md](DEFINICAO.md) |
| Comprar | [LISTA-DE-COMPRAS.md](LISTA-DE-COMPRAS.md) |
| Fases e critério de pronto de cada uma | [PLANO.md](PLANO.md) |
| Servidor local (opção B) | [servidor/README.md](servidor/README.md) |
| Programa da placa | [firmware/README.md](firmware/README.md) |
| Perguntas e limites (API, placas, câmera, movimento) | [FAQ.md](FAQ.md) |
| Ideias: a placa como cabeça de outros robôs (6 exemplos ilustrados) | [IDEIAS-CORPOS.md](IDEIAS-CORPOS.md) |
| Versão anterior (XIAO soldada num cubo de 40 mm) | [arquivo/variante-xiao/](arquivo/variante-xiao/DEFINICAO.md) |
| Retomar o trabalho | [handoffs/latest.md](handoffs/latest.md) |

## Em números

- Placa: 54 × 54 × 16,5 mm, 54 g. Tela de 2", 320 × 240, com toque. Câmera de 0,3 MP. Bateria de 200 mAh.
- Preço: R$ 256,55 na loja oficial M5Stack do AliExpress (lido em 15/11/2026, sem frete nem imposto).
- Áudio: 16 kHz, 16 bits, mono, nos dois sentidos. Fala de até 15 s.
- Opção B, medido em 15/11: primeiro som em 6,8 a 7,6 s com a resposta por partes (quente), 19 s do toque no caso frio. Detalhe em [servidor/MEDIDAS.md](servidor/MEDIDAS.md).

## O processo, do início ao fim

Legenda: 🧠 sessão com o Nei · ⚙️ comando/script · 🤖 `claude -p`

| # | Passo | Comando | Quem | Existe hoje? |
|---|---|---|---|---|
| 1 | Ler a definição e escolher voz e opção | [DEFINICAO.md](DEFINICAO.md), seção 3 | 🧠 | sim |
| 2 | Comprar a CoreS3 Lite | [LISTA-DE-COMPRAS.md](LISTA-DE-COMPRAS.md) | 🧠 | sim |
| 3 | Copiar o `.env` do servidor e escolher o token | `cp servidor/env.exemplo servidor/.env` | 🧠 | sim |
| 4 | Subir o servidor (opção B); ele sobe o Whisper e a voz residentes | `python3 servidor/servidor.py` | ⚙️ | sim |
| 5 | Testar o servidor sem o robô, com e sem foto | `python3 servidor/testar.py servidor/teste/pergunta.wav` (e `--foto`, `--limites`) | ⚙️ | sim |
| 5b | Gravar as frases de espera na voz do robô (só uma vez, ou ao trocar a voz) | `python3 servidor/gerar_espera.py` | ⚙️ | sim (32 frases) |
| 6 | Dentro de cada turno: escrever a resposta | `claude -p --model haiku --tools "" --strict-mcp-config --no-session-persistence …` | 🤖 | comando testado |
| 7 | Instalar as bibliotecas da placa (avisar o Nei) | `arduino-cli lib install M5Unified M5GFX` | ⚙️ | não: fase F2 |
| 8 | Preencher Wi-Fi, servidor, token e cérebro | `cp firmware/robo_fala/segredos.exemplo.h firmware/robo_fala/segredos.h` | 🧠 | sim |
| 9 | Compilar o firmware | `arduino-cli compile --fqbn esp32:esp32:m5stack_cores3 firmware/robo_fala` | ⚙️ | sim (esqueleto) |
| 10 | Gravar na placa | `arduino-cli upload --fqbn esp32:esp32:m5stack_cores3 -p /dev/ttyACM0 firmware/robo_fala` | ⚙️ | não testado: sem placa |
| 11 | Conversar na bancada: 5 perguntas seguidas | [PLANO.md](PLANO.md), fase F2 | 🧠 | — |
| 12 | Opção A, direto na API | só com autorização do Nei: [PLANO.md](PLANO.md), fase F3 | 🧠 | — |
| 13 | Visão: foto e poucos quadros | [PLANO.md](PLANO.md), fase F4 | 🧠 | — |
| 14 | Guia PT/EN/ES em `guia/` (skill `projetos-landing-guia`, tradução pelo `inema-traduz`, revisor independente) | `guia/index.html`, `guia/en/`, `guia/es/` | 🧠 + 🤖 | sim (15/11/2026) |
| 15 | Publicar: push no `main`; o GitHub Pages sai pelo Actions | `git push` → https://inematds.github.io/robo-cores3-lite/guia/ | ⚙️ | sim |
| 16 | Portal inema.club, inemabuscas e catálogo PRO | skill `atualiza-portal` | 🧠 | sim — [PUBLICACAO.md](PUBLICACAO.md) |
| 17 | Tópico no grupo INEMA.ROBOT do Telegram + MENU | skill `postar-telegram` | 🧠 | sim — [PUBLICACAO.md](PUBLICACAO.md) |
| 18 | Vídeo no canal lives6 e no guia | outro agente; marca `<!-- VIDEO: -->` no guia | 🧠 | sim (15/11/2026) — [lives6](https://www.youtube.com/watch?v=ckhcNbClXNs) |

No robô, o único passo com `claude -p` é o 6, pela assinatura, sem ferramentas. O 🤖 do passo 14 é a tradução e o revisor.

## Regras

- Nenhuma API externa sem autorização explícita do Nei (serviço e finalidade). A opção A existe só no papel.
- Claude só pela assinatura (`claude -p`), nunca por chave de API.
- Repo público em https://github.com/inematds/robo-cores3-lite (publicado por ordem do Nei em 15/11/2026).
