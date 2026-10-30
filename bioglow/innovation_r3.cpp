#include <Arduino.h>

#include <OneWire.h>
#include <DallasTemperature.h>
#include <GravityTDS.h>

constexpr uint8_t TDS_PIN = A1;
constexpr uint8_t TEMPERATURE_PIN = 2;
constexpr uint8_t TURBIDITY_PIN = A2;

constexpr float ADC_MAX = 1023.0f;
constexpr float VREF = 5.0f;

constexpr uint32_t READ_INTERVAL_MS = 1000;
constexpr uint8_t TURBIDITY_SAMPLES = 32;

OneWire wire(TEMPERATURE_PIN);
DallasTemperature probe(&wire);
GravityTDS tds;

uint32_t lastRead = 0;

void setup() {
  Serial.begin(115200);

  probe.begin();
  probe.setResolution(12);
  probe.setWaitForConversion(false);
  probe.requestTemperatures();

  tds.setPin(TDS_PIN);
  tds.setAref(VREF);
  tds.setAdcRange(ADC_MAX + 1);
  tds.begin();

  lastRead = millis();
}

void loop() {
  if (millis() - lastRead < READ_INTERVAL_MS) return;
  lastRead = millis();

  float temp = probe.getTempCByIndex(0);
  probe.requestTemperatures();

  uint32_t turbiditySum = 0;
  for (uint8_t i = 0; i < TURBIDITY_SAMPLES; i++) {
    turbiditySum += analogRead(TURBIDITY_PIN);
  }
  float turbidityV = (turbiditySum / (float)TURBIDITY_SAMPLES) * (VREF / ADC_MAX);

  if (isnan(temp) || temp == DEVICE_DISCONNECTED_C) {
    Serial.print(F("Temp sensor error; TDS unavailable."));
    probe.begin();
    probe.setWaitForConversion(false);
    probe.requestTemperatures();
  } else {
    tds.setTemperature(temp);
    tds.update();
    float ppm = tds.getTdsValue();

    Serial.print(F("Temperature: "));
    Serial.print(temp, 2);
    Serial.print(F(" C | TDS: "));
    if (isnan(ppm) || ppm < 0) Serial.print(F("invalid"));
    else { Serial.print(ppm, 0); Serial.print(F(" ppm")); }
  }

  Serial.print(F(" | Turbidity: "));
  Serial.print(turbidityV, 3);
  Serial.println(F(" V"));
}
