# CLAUDE.md — robo-esp32-fala

Cubo de mesa de 40 mm com um ESP32 (XIAO ESP32S3) que só conversa por voz: grava a fala, manda para um servidor
local na máquina do Nei e toca a resposta. Sem motor, sem servo, sem rodas.
Pedido do Nei: "uma solução simples usando ESP32 e ele apenas falando comigo através de uma API, um robô o menor
possível, quadrado, sem movimentação".

- Repo futuro: `inematds/robo-esp32-fala`. **Hoje é só local: sem remoto, sem push, até o Nei mandar.**
- Autor dos commits: `inematds <inematds@gmail.com>` (já configurado neste repo).
- Projeto separado do `~/projetos/robos-impressos`. De lá só se lê e se copia; não editar aquela pasta daqui.

## Ao começar uma sessão
1. Ler `handoffs/latest.md`.
2. Ler `DEFINICAO.md` (o que é, o que foi decidido e por quê) e a fase atual no `PLANO.md`.

## Comandos
- Tamanho do cubo: `python3 cad/caixa_minima.py` (medidas em `cad/parametros.py`).
- Compilar o firmware: `arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi firmware/robo_fala`.
- Gravar: `arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi -p <porta> firmware/robo_fala`.
- Servidor (a partir da F1): `python3 servidor/servidor.py` e `python3 servidor/testar.py servidor/teste/pergunta.wav`.
- Saúde do inemavox: `GET http://127.0.0.1:8010/api/health`.

## Regras do projeto
- **Nenhuma API externa sem autorização explícita do Nei** (OpenAI, Groq, ElevenLabs, Edge TTS, qualquer nuvem).
  GitHub e Telegram seguem a regra global.
- **Claude só pela assinatura:** `claude -p`, nunca com `--bare`, sempre com `env -u ANTHROPIC_API_KEY`.
- **`claude -p` do robô sempre sem ferramentas:** `--tools "" --strict-mcp-config --no-session-persistence`.
  A entrada é fala transcrita de qualquer pessoa.
- **Voz só pela rota `/api/jobs/tts/upload` do inemavox** (Chatterbox local). A rota `/api/jobs/tts` sem `engine`
  e o `chatterbox-vc` usam o Edge, que é serviço online.
- **Nenhum modelo local novo** (Whisper, TTS, LLM, palavra de ativação) sem aprovação do Nei.
- Não instalar PlatformIO nem ESP-IDF: o `arduino-cli` com o core `esp32:esp32` 3.3.12 já resolve.
- Toda medida de componente mora em `cad/parametros.py`, com a fonte: P (fabricante), T (loja), NC (não confirmado).
  Mudou uma medida: rodar `cad/caixa_minima.py` e atualizar a DEFINICAO.md, seção 12, no mesmo commit.
- Caixa: cabe em 256 mm, parede de 2,0 mm ou mais, sem suporte sempre que der, reforço nos pontos de carga.
- Segredos fora do git: `servidor/.env` e `firmware/robo_fala/segredos.h`.
- Tradução só por `inema-traduz`. Página e guia: ler antes `~/projetos/inema-design/DESIGN.md`.
- Número sem fonte não entra em documento. Preço sem leitura em loja leva "estimativa, não conferida".
- Commit a cada pacote verificado. Mudou o fluxo: atualizar a seção "O processo, do início ao fim" do README no
  mesmo commit.
- Falha corrigida: uma linha no `FALHAS.md`. Limite de ambiente: uma linha em `~/projetos/wifi/LIMITES.md`.

## Self-learning
Quando o Nei corrigir ou você notar um erro: antes de seguir, escreva a lição como uma linha no TOPO da seção
Lessons abaixo.

## Lessons
