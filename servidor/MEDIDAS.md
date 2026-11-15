# MEDIDAS — tempos do servidor (opção B)

Segundos. stt = Whisper residente, llm = claude -p, tts = voz residente.

| quando | teste | foto | stt | llm | tts | total | ouvido |
|---|---|---|---|---|---|---|---|
| 15/11/2026 00:49:38 | pergunta.wav | não | 0.7 | 5.2 | 5.2 | 11.3 | Que horas são em Tóquio? |
| 15/11/2026 00:49:56 | pergunta-visao.wav | sim | 0.4 | 4.2 | 11.2 | 15.9 | O que você está vendo? |
| 15/11/2026 00:50:21 | pergunta.wav | não | 1.2 | 5.7 | 6.7 | 13.8 | Que horas são em Tóquio? |
| 15/11/2026 00:50:34 | pergunta.wav | não | 0.6 | 4.4 | 6.6 | 11.6 | Que horas são em Tóquio? |
| 15/11/2026 00:50:46 | pergunta.wav | não | 0.5 | 4.3 | 5.3 | 10.1 | Que horas são em Tóquio? |
| 15/11/2026 00:51:39 | pergunta.wav | não | 12.4 | 4.6 | 16.1 | 33.2 | Que horas são em Tóquio? |

Notas (15/11/2026):
- As linhas de 00:49 a 00:50 são com os serviços residentes já no ar ("quente"): **10,1 a 13,8 s** sem foto,
  15,9 s com foto (a resposta com foto foi mais longa: a voz demora mais).
- A última linha é "fria": Whisper e voz residentes desligados antes, subidos pelo servidor no próprio turno
  (whisper 12,4 s, voz 16,1 s): **33,2 s**. Acontece na primeira pergunta depois de 10 min parado.
- Antes dos serviços residentes, pela fila de jobs do inemavox: transcrição 12,1 s e voz de 14 a 28 s por frase.
- A voz cresce com o tamanho da resposta (~1,3 a 1,8 s de geração por segundo de fala).
