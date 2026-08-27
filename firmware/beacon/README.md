# Beacon firmware

Flash `beacon.ino` with the Arduino IDE or arduino-cli.

**Wemos D1 mini (ESP8266):** board "LOLIN(WEMOS) D1 R2 & mini", 115200 upload.
Wire an LED from **D1 (GPIO5)** through 220–330 Ω to GND (optional 850 nm IR
LED in parallel with its own resistor). The onboard LED (D4/GPIO2, active-low)
works for a bench test: compile with `-DLED_PIN=2 -DLED_ACTIVE_LOW=1`.

Serial device on Linux: usually `/dev/ttyUSB0` (CH340). Test:

    uv run python -m slimevr_camera.recorder.beacon /dev/ttyUSB0 /tmp/beacon.csv --duration 20

You should see the LED blink in 200 ms symbols and `/tmp/beacon.csv` fill
with transitions. Then place it where **both** cameras see it, unobstructed
by the play space.
