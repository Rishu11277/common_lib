#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <GravityTDS.h>

const int TEMP_PIN = 2;
const int TURBIDITY_PIN = A3;
const int TDS_PIN = A4;

const int ADC_BITS = 14;
const float VREF = 5.0;
const float ADC_MAX = 16383.0;

const int GROUPS = 128;
const int GROUP_SIZE = 64;
const float TRIM_FRACTION = 0.10;
const int TRIM = GROUPS * TRIM_FRACTION;

const float TURBIDITY_OFFSET = 0.0;
const float TURBIDITY_LIMIT = 10.0;
const float TDS_LIMIT = 500.0;
const float HYSTERESIS = 0.9;

const float NTU_A = -1120.4;
const float NTU_B = 5742.3;
const float NTU_C = -4352.9;
const float NTU_MIN_VOLTAGE = 2.5;
const float NTU_MAX = 3000.0;

const float TEMP_MIN = -5.0;
const float TEMP_MAX = 80.0;

const unsigned long READ_INTERVAL_MS = 1000;

enum Status { GOOD, BAD, UNKNOWN, UNKNOWN_GOOD, UNKNOWN_BAD };

OneWire wire(TEMP_PIN);
DallasTemperature probe(&wire);
GravityTDS tds;

bool turbidityBad = false;
bool tdsBad = false;
bool turbidityRemembered = false;
bool tdsRemembered = false;
unsigned long lastRead = 0;

float readTurbiditySample() {
  return analogRead(TURBIDITY_PIN) * VREF / ADC_MAX;
}

float readTdsSample() {
  tds.update();
  return tds.getTdsValue();
}

float measure(float (*readSample)()) {
  float groups[GROUPS];

  for (int g = 0; g < GROUPS; g++) {
    float sum = 0;
    for (int i = 0; i < GROUP_SIZE; i++) sum += readSample();
    float average = sum / GROUP_SIZE;

    int i = g - 1;
    while (i >= 0 && groups[i] > average) {
      groups[i + 1] = groups[i];
      i--;
    }
    groups[i + 1] = average;
  }

  float sum = 0;
  for (int g = TRIM; g < GROUPS - TRIM; g++) sum += groups[g];
  return sum / (GROUPS - 2 * TRIM);
}

float readTemperature() {
  float temp = probe.getTempCByIndex(0);
  probe.requestTemperatures();
  return temp;
}

bool isValidTemperature(float temp) {
  return !isnan(temp) && temp > TEMP_MIN && temp < TEMP_MAX;
}

float voltageToNtu(float voltage) {
  if (voltage < NTU_MIN_VOLTAGE) return NTU_MAX;
  return max(0.0f, NTU_A * voltage * voltage + NTU_B * voltage + NTU_C);
}

bool updateAlarm(bool valid, bool wasBad, float value, float limit) {
  if (!valid) return wasBad;
  return value >= limit * (wasBad ? HYSTERESIS : 1.0);
}

Status getStatus(bool turbidityValid, bool tdsValid) {
  if ((turbidityValid && turbidityBad) || (tdsValid && tdsBad)) return BAD;
  if (turbidityValid && tdsValid) return GOOD;

  bool missingRemembered = (turbidityValid || turbidityRemembered) && (tdsValid || tdsRemembered);
  if (!missingRemembered) return UNKNOWN;

  bool rememberedBad = (!turbidityValid && turbidityBad) || (!tdsValid && tdsBad);
  return rememberedBad ? UNKNOWN_BAD : UNKNOWN_GOOD;
}

void printReadings(float temp, float ppm, float ntu, float voltage, Status status) {
  Serial.print("Temp: ");
  if (isValidTemperature(temp)) Serial.print(temp);
  else Serial.print("UNKNOWN");
  Serial.print(" C | TDS: ");
  if (isnan(ppm)) Serial.print("UNKNOWN");
  else Serial.print(ppm);
  Serial.print(" ppm | Turbidity: ");
  if (isnan(ntu)) Serial.print("UNKNOWN");
  else Serial.print(ntu);
  Serial.print(" NTU (");
  Serial.print(voltage, 4);
  Serial.print(" V) | ");

  if (status == GOOD) Serial.println("GOOD");
  else if (status == BAD) Serial.println("BAD");
  else if (status == UNKNOWN_GOOD) Serial.println("UNKNOWN/GOOD");
  else if (status == UNKNOWN_BAD) Serial.println("UNKNOWN/BAD");
  else Serial.println("UNKNOWN");
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(ADC_BITS);
  probe.begin();
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

  float temp = readTemperature();
  bool tempValid = isValidTemperature(temp);

  float voltage = measure(readTurbiditySample) + TURBIDITY_OFFSET;
  float ntu = voltageToNtu(voltage);
  bool turbidityValid = !isnan(ntu);

  float ppm = NAN;
  if (tempValid) {
    tds.setTemperature(temp);
    ppm = measure(readTdsSample);
  }
  bool tdsValid = !isnan(ppm) && ppm >= 0;
  if (!tdsValid) ppm = NAN;

  turbidityBad = updateAlarm(turbidityValid, turbidityBad, ntu, TURBIDITY_LIMIT);
  tdsBad = updateAlarm(tdsValid, tdsBad, ppm, TDS_LIMIT);
  turbidityRemembered = turbidityRemembered || turbidityValid;
  tdsRemembered = tdsRemembered || tdsValid;

  printReadings(temp, ppm, ntu, voltage, getStatus(turbidityValid, tdsValid));
}