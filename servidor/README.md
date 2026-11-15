# servidor — a parte que entende, pensa e fala

**Ainda não existe código aqui.** Este arquivo diz o que vai ter e dá a receita da fase F1 do
[PLANO.md](../PLANO.md). O protocolo completo está na [DEFINICAO.md](../DEFINICAO.md), seção 11. Este servidor é a **opção B** do robô
(a opção A, direto numa API, está na seção 10 e não passa por aqui, a não ser na variante A2).

O servidor roda na máquina do Nei e não chama nenhum serviço de fora: fala só com `127.0.0.1`.

## O que vai ter

| Arquivo | O que é |
|---|---|
| `servidor.py` | Servidor HTTP na porta 8770. Só biblioteca padrão do Python (`http.server`, `urllib`, `subprocess`): nada a instalar |
| `testar.py` | Manda um WAV ao servidor e confere a resposta (formato, volume, texto, tempos). É o validador da F1 |
| `persona.txt` | Quem o robô é e como responde. Vira o `--system-prompt` do `claude -p` |
| `env.exemplo` | Modelo do `.env` (já existe) |
| `.env` | Suas configurações e o token. Fora do git |
| `teste/pergunta.wav` | Gravação de teste, 5 s |
| `teste/pergunta-visao.wav` e `teste/foto.jpg` | Teste de pergunta com foto ("o que você está vendo?") |
| `dados/` | Turnos gravados e histórico da conversa. Fora do git |
| `MEDIDAS.md` | Tempos medidos de cada etapa, com data |

## Rotas

| Rota | O que faz |
|---|---|
| `GET /saude` | Devolve `{"ok": true}` |
| `POST /v1/foto` | Recebe um JPEG de até 200 kB, guarda por 60 s e devolve `{"turno": "<id>"}` |
| `POST /v1/fala` | Recebe um WAV 16 kHz mono 16 bits (com `X-Turno` se houve foto), devolve um WAV no mesmo formato com a resposta falada |

Códigos de resposta, cabeçalhos e limites: DEFINICAO.md, seção 11.

## Receita de um turno (o que o `servidor.py` faz)

1. **Confere** o token (`X-Robo-Token`), o tamanho (até 1 MB) e o formato do WAV. Grava em
   `dados/turnos/<data-hora>/pergunta.wav`. Mede a duração e o volume médio (`ffmpeg -af volumedetect`):
   menos de 0,5 s ou volume médio abaixo de −50 dB → resposta 204, sem chamar o Whisper. O Whisper costuma
   inventar texto em áudio de silêncio, então a trava fica antes dele. O limite de −50 dB é ponto de partida:
   a F1 ajusta com gravações reais.
2. **Transcreve** pelo inemavox. Dois caminhos; a F1 mede os dois e fica com o mais rápido:
   - Fila de jobs, `http://127.0.0.1:8010`: `POST /api/jobs/transcribe/upload` com o arquivo em `file` e
     `config_json` com `{"asr_engine": "whisper", "whisper_model": "large-v3", "src_lang": "pt"}`. Acompanhar em
     `GET /api/jobs/{id}` até `status` ser `completed` ou `failed`. Texto em `GET /api/jobs/{id}/transcript?format=txt`.
   - Whisper residente, `http://127.0.0.1:7871`: `POST /transcrever` com `{"audio": "<caminho>", "lang": "pt"}`.
     O modelo fica na memória e sai sozinho depois de 600 s parado. Sobe com
     `~/miniconda3/envs/chatterbox/bin/python3 ~/projetos/inemavox/whisper_daemon.py`.
   - Transcrição vazia → resposta 204 também, sem chamar as etapas seguintes.
3. **Responde** com o `claude -p`, pela assinatura, sem ferramentas, numa pasta vazia:
   ```
   cd servidor/dados/vazio && env -u ANTHROPIC_API_KEY claude -p --model haiku --tools "" \
     --strict-mcp-config --no-session-persistence \
     --system-prompt "$(cat ../../persona.txt)" "<histórico curto + fala de agora>"
   ```
   Testado em 14/11/2026 com uma pergunta curta: respondeu em 5,0 s.
   **Com foto (`X-Turno`):** a imagem precisa chegar ao Claude sem liberar ferramentas. Candidato, não testado:
   `--input-format stream-json --output-format stream-json` com uma mensagem que leva um bloco de imagem em base64.
   A F1 prova (teste 6). Se só funcionar liberando uma ferramenta, parar e levar ao Nei.
4. **Gera a voz** pelo inemavox, com o Chatterbox local: `POST /api/jobs/tts/upload` com o WAV de referência da
   voz em `file` e `config_json` com `{"text": "<resposta>", "lang": "pt"}`. Acompanhar em `GET /api/jobs/{id}`.
   Áudio em `GET /api/jobs/{id}/audio`.
5. **Converte** com `ffmpeg -ar 16000 -ac 1 -c:a pcm_s16le` e devolve o WAV, com os cabeçalhos `X-Ouvido`,
   `X-Resposta` e `X-Tempos`.
6. **Guarda** a troca em `dados/conversa-<robo-id>.json` (as últimas 6 entram no próximo pedido).

Rotas e campos lidos em `~/projetos/inemavox/api/server.py` e `api/job_manager.py` em 14/11/2026. Nenhuma
transcrição nem voz foi gerada para este projeto: a F1 confere na prática.

## Travas (não negociar sem o Nei)

- **Voz só por `/api/jobs/tts/upload`.** A rota `/api/jobs/tts` sem o campo `engine` usa `edge`, o serviço online
  da Microsoft. `chatterbox-vc` também passa pelo Edge. Os dois são API externa.
- **`claude -p` nunca com `--bare`:** esse modo só aceita chave de API. Sempre com `env -u ANTHROPIC_API_KEY`.
- **`claude -p` sempre com `--tools ""`**, `--strict-mcp-config` e `--no-session-persistence`. O texto de entrada
  é fala transcrita de qualquer pessoa perto do robô.
- **Token obrigatório.** O servidor escuta na rede de casa.
- **Nenhum modelo local novo** (outro Whisper, outro TTS, outro LLM) sem aprovação do Nei.
- **Não apagar nada em `~/projetos/inemavox/jobs/`.** Cada turno cria duas pastas lá; a limpeza é assunto do inemavox.

## Persona (rascunho para o `persona.txt`)

- Responde em português do Brasil, em uma ou duas frases curtas.
- Sem markdown, sem lista, sem emoji: o texto vira voz.
- Número e ano por extenso ("dois mil e vinte e seis"): o Chatterbox lê "2026" como "2006".
- Não sabe a hora nem a data sozinho: o servidor escreve a data e a hora no começo do pedido.
- Quando não sabe, diz que não sabe.

## O que medir na F1

- Tempo de cada etapa nos dois caminhos de transcrição, com o modelo frio e com o modelo já carregado.
- Quanto do `claude -p` é espera de partida. Testar também `--setting-sources` para não carregar os ganchos e o
  `CLAUDE.md` global (não testado; conferir que a assinatura continua valendo).
- Se a fila de jobs do inemavox e a fila `~/projetos/wifi/scripts/fila-vaga gpu` se enxergam, ou se dois trabalhos
  de GPU podem bater.
- Tamanho de `~/projetos/inemavox/jobs/` antes e depois de 20 turnos.
