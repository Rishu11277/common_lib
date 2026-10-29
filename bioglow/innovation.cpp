// JUST THE SENSOR CODE! NO MOTOR FUNCTIONALITY (Uno R3)
#include <OneWire.h>
#include <DallasTemperature.h>
#include <GravityTDS.h>

const uint8_t TDS_PIN = A1;
const uint8_t TEMPERATURE_PIN = 2;

OneWire wire(TEMPERATURE_PIN);
DallasTemperature probe(&wire);
GravityTDS tds;

void setup() {
  Serial.begin(115200);
  probe.begin();

  tds.setPin(TDS_PIN);
  tds.setAref(5.0);       // Uno R3 runs at 5V
  tds.setAdcRange(1024);  // Uno R3 ADC is 10-bit
  tds.begin();

  Serial.println(F("Calibration: use Newline; send enter, cal:707, exit separately."));
  Serial.println(F("Use cal:707 only with 707 ppm calibration solution."));
}

void loop() {
  probe.requestTemperatures();
  float temp = probe.getTempCByIndex(0);

  if (isnan(temp) || temp == DEVICE_DISCONNECTED_C) {
    Serial.println(F("Temperature sensor error; TDS unavailable."));
    probe.begin();  // try to re-detect the sensor
  } else if (temp < 0 || temp > 55) {
    Serial.println(F("Temperature outside 0-55 C; TDS unavailable."));
  } else {
    tds.setTemperature(temp);
    tds.update();
    float ppm = tds.getTdsValue();

    if (isnan(ppm) || ppm < 0) {
      Serial.println(F("Invalid TDS reading."));
    } else {
      Serial.print(F("Temperature: "));
      Serial.print(temp, 2);
      Serial.print(F(" C | TDS: "));
      Serial.print(ppm, 0);
      Serial.println(F(" ppm"));
    }
  }

  delay(1000);
}