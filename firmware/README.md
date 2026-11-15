# firmware — o programa do ESP32

**Hoje só existe o esqueleto:** `robo_fala/robo_fala.ino` pisca o LED e mostra o tamanho da PSRAM. Ele compila
(conferido em 14/11/2026: 277 587 bytes, 8% do espaço). Gravar, enviar e tocar entram nas fases F2 e F3 do
[PLANO.md](../PLANO.md). Pinos e protocolo: [DEFINICAO.md](../DEFINICAO.md), seções 9 e 11.

## Ferramenta escolhida: Arduino pelo `arduino-cli`

| Opção | Estado nesta máquina | Decisão |
|---|---|---|
| **Arduino (core `esp32:esp32` 3.3.12) pelo `arduino-cli` 1.5.1** | Instalado. A placa `XIAO_ESP32S3` já aparece | **Escolhida:** nada a instalar, roda por comando, as bibliotecas necessárias vêm no core |
| PlatformIO | Não instalado | Fica de fora: seria uma instalação a mais para o mesmo resultado |
| ESP-IDF | Não instalado | Fica de fora: mais controle do áudio, mas instalação grande e código mais longo. Só se o Arduino não der conta |

Bibliotecas, todas dentro do core instalado: `WiFi`, `HTTPClient`, `ESP_I2S` (microfone e amplificador; exemplo
`Record_to_WAV`) e, se a palavra de ativação entrar um dia, `ESP_SR` (não testada).

## Comandos

```
# compilar (na raiz do repo)
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi firmware/robo_fala

# descobrir a porta da placa
arduino-cli board list

# gravar
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi -p /dev/ttyACM0 firmware/robo_fala

# ver as mensagens
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```

**`PSRAM=opi` é obrigatório.** O padrão da placa no `arduino-cli` é PSRAM desligada. Sem essa opção o programa
compila, mas a gravação da fala (até 480 kB) não cabe na memória. O esqueleto avisa pela serial quando a PSRAM
está desligada.

Os comandos de gravar e de monitor não foram testados: ainda não há placa.

## Segredos

Copie `robo_fala/segredos.exemplo.h` para `robo_fala/segredos.h` e preencha a rede Wi-Fi, o endereço do servidor e o
token. O `segredos.h` está no `.gitignore`.

## O que o firmware vai fazer (F2 e F3)

1. Liga, conecta no Wi-Fi e chama `GET /saude`.
2. Botão apertado: grava do INMP441 para um bloco da PSRAM (16 kHz, 16 bits, mono), até 15 s.
3. Botão solto: escreve o cabeçalho WAV e manda com `POST /v1/fala`.
4. Resposta 200: lê o WAV aos pedaços e manda para o MAX98357A enquanto chega.
5. LED da placa (GPIO21) mostra o estado: pronto, gravando, pensando, falando, erro.

Estados: `PRONTO` → `GRAVANDO` → `PENSANDO` → `FALANDO` → `PRONTO`. Falha: `ERRO` por 2 s e volta a `PRONTO`.

## Pontos de atenção

- O INMP441 costuma entregar 24 bits dentro de palavras de 32 (dito de memória: a ficha não foi lida, veja a
  DEFINICAO.md, seção 14). O firmware converte para 16 bits antes de guardar. O deslocamento certo se acerta na
  bancada, olhando o volume da gravação (teste 5 da F2).
- Se o amplificador estalar ao ligar e desligar, manter o I²S aberto mandando silêncio.
- Com a XIAO Sense (plano B), o microfone é PDM nos GPIO 42 (relógio) e 41 (dado): muda o modo do `ESP_I2S`.
- O programa só usa o Wi-Fi de 2,4 GHz (a placa não tem 5 GHz).
