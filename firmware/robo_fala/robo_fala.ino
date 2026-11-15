// robo-esp32-fala: esqueleto. Só confere a placa: PSRAM ligada e LED piscando.
// O firmware de verdade (gravar, enviar, tocar) entra nas fases F2 e F3 do PLANO.md.
//
// Compilar (na raiz do repo):
//   arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi firmware/robo_fala
// Sem "PSRAM=opi" a placa compila com a PSRAM desligada e a gravação da fala não cabe na memória.

#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  delay(1500);
  Serial.printf("robo-esp32-fala esqueleto | PSRAM: %u bytes | heap livre: %u bytes\n",
                (unsigned)ESP.getPsramSize(), (unsigned)ESP.getFreeHeap());
  if (ESP.getPsramSize() == 0) {
    Serial.println("ERRO: PSRAM desligada. Compile com PSRAM=opi (veja firmware/README.md).");
  }
}

void loop() {
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  delay(500);
}
