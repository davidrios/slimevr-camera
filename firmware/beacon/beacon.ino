// Sync beacon: host-driven LED over USB serial.
// Tested targets: Wemos D1 mini (ESP8266, Arduino core), any ESP32/Arduino.
// Protocol (115200 8N1): host sends '1' -> LED on, '0' -> LED off, '?' -> "pong <micros>".
// Every accepted command is echoed as "<c> <micros>\n" so the host can measure latency.
//
// Wemos D1 mini wiring: external LED on D1 (GPIO5) -> 220-330 ohm -> LED -> GND.
//   (Optional second 850 nm IR LED in parallel with its own resistor; IR only shows in
//    the cameras' night mode, visible works in both. Keep it modest: no blooming.)
//   The onboard blue LED (D4 / GPIO2) is ACTIVE-LOW; it works as a quick test with
//   LED_ACTIVE_LOW 1 but is dim and half-covered — use the external LED for real runs.
// Note: opening the serial port toggles DTR/RTS and resets the board; the host driver
// waits 2 s after opening before sending symbols.
#ifndef LED_PIN
#define LED_PIN 5          // D1 on Wemos D1 mini
#endif
#ifndef LED_ACTIVE_LOW
#define LED_ACTIVE_LOW 0   // set 1 for the onboard LED on GPIO2
#endif
static inline void led(bool on) { digitalWrite(LED_PIN, (on ^ LED_ACTIVE_LOW) ? HIGH : LOW); }
void setup() { pinMode(LED_PIN, OUTPUT); led(false); Serial.begin(115200); }
void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '1' || c == '0') { led(c == '1'); Serial.print(c); Serial.print(' '); Serial.println(micros()); }
    else if (c == '?') { Serial.print("pong "); Serial.println(micros()); }
  }
}
