#include <OneWire.h>
#include <DallasTemperature.h>
#include <GravityTDS.h>
#include <math.h>

OneWire wire(2);
DallasTemperature probe(&wire);
GravityTDS tds;

void setup() {
  Serial.begin(115200);
  analogReadResolution(10);
  probe.begin();

  tds.setPin(A1);
  tds.setAref(5.0);
  tds.setAdcRange(1024);
  tds.begin();

  Serial.println("Calibration: use Newline; send enter, cal:707, exit separately.");
  Serial.println("Use cal:707 only with 707 ppm calibration solution.");
}

void loop() {
  DeviceAddress address;
  float temp = DEVICE_DISCONNECTED_C;

  if (probe.getAddress(address, 0)) {
    if (probe.requestTemperaturesByAddress(address).result) {
      temp = probe.getTempC(address);
    }
  }

  if (!isfinite(temp) || temp == DEVICE_DISCONNECTED_C) {
    tds.cancelCalibration();
    Serial.println("Temperature sensor error; TDS unavailable.");
    probe.begin();
  } else if (temp < 0 || temp > 55) {
    tds.cancelCalibration();
    Serial.println("Temperature outside 0-55 C; TDS unavailable.");
  } else {
    tds.setTemperature(temp);
    tds.update();
    float ppm = tds.getTdsValue();

    if (!isfinite(ppm) || ppm < 0) {
      tds.cancelCalibration();
      Serial.println("Invalid TDS reading.");
    } else {
      Serial.print("Temperature: ");
      Serial.print(temp, 2);
      Serial.print(" C | TDS: ");
      Serial.print(ppm, 0);
      Serial.println(" ppm");
    }
  }

  delay(1000);
}
#include <OneWire.h>
#include <DallasTemperature.h>
#include <GravityTDS.h>
#include <math.h>

OneWire wire(2);
DallasTemperature probe(&wire);
GravityTDS tds;

void setup() {
  Serial.begin(115200);
  analogReadResolution(10);
  probe.begin();

  tds.setPin(A1);
  tds.setAref(5.0);
  tds.setAdcRange(1024);
  tds.begin();

  Serial.println("Calibration: use Newline; send enter, cal:707, exit separately.");
  Serial.println("Use cal:707 only with 707 ppm calibration solution.");
}

void loop() {
  DeviceAddress address;
  float temp = DEVICE_DISCONNECTED_C;

  if (probe.getAddress(address, 0)) {
    if (probe.requestTemperaturesByAddress(address).result) {
      temp = probe.getTempC(address);
    }
  }

  if (!isfinite(temp) || temp == DEVICE_DISCONNECTED_C) {
    tds.cancelCalibration();
    Serial.println("Temperature sensor error; TDS unavailable.");
    probe.begin();
  } else if (temp < 0 || temp > 55) {
    tds.cancelCalibration();
    Serial.println("Temperature outside 0-55 C; TDS unavailable.");
  } else {
    tds.setTemperature(temp);
    tds.update();
    float ppm = tds.getTdsValue();

    if (!isfinite(ppm) || ppm < 0) {
      tds.cancelCalibration();
      Serial.println("Invalid TDS reading.");
    } else {
      Serial.print("Temperature: ");
      Serial.print(temp, 2);
      Serial.print(" C | TDS: ");
      Serial.print(ppm, 0);
      Serial.println(" ppm");
    }
  }

  delay(1000);
}
