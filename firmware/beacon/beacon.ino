// Sync beacon: host-driven LED over USB serial. Works on any Arduino/ESP32 board.
// Protocol (115200 8N1): host sends '1' -> LED on, '0' -> LED off, '?' -> replies "pong <micros>".
// Every accepted command is echoed as "<c> <micros>\n" so the host can measure round-trip latency.
// Wire: LED_PIN -> resistor -> LED (visible) and optionally a second 850 nm IR LED in parallel
// (IR only shows in the cameras' night mode; visible works in both). Keep both modest: no blooming.
#ifndef LED_PIN
#define LED_PIN 2
#endif
void setup() { pinMode(LED_PIN, OUTPUT); digitalWrite(LED_PIN, LOW); Serial.begin(115200); }
void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '1' || c == '0') { digitalWrite(LED_PIN, c == '1' ? HIGH : LOW); Serial.print(c); Serial.print(' '); Serial.println(micros()); }
    else if (c == '?') { Serial.print("pong "); Serial.println(micros()); }
  }
}
