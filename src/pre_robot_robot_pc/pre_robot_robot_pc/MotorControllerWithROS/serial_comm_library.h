#pragma once

#include <ArduinoJson.h>

SemaphoreHandle_t serialMutex = xSemaphoreCreateMutex();

void send_serial_motor_rpm_feedback(float L_rpm, float R_rpm) {
  StaticJsonDocument<1024> doc;
  doc["feedback_type"] = "motor_rpm";
  doc["data"]["L"] = L_rpm;
  doc["data"]["R"] = R_rpm;

  if (xSemaphoreTake(serialMutex, portMAX_DELAY)) {
    serializeJson(doc, Serial);
    Serial.println();
    xSemaphoreGive(serialMutex);
  }
}

void send_serial_debug_msg_feedback(const String& msg) {
  StaticJsonDocument<1024> doc;
  doc["feedback_type"] = "debug_msg";
  doc["data"]["msg"] = msg;

  if (xSemaphoreTake(serialMutex, portMAX_DELAY)) {
    serializeJson(doc, Serial);
    Serial.println();
    xSemaphoreGive(serialMutex);
  }
}