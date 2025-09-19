#include "motor_library.h"
#include "serial_comm_library.h"

// Define LED pin
#define LED_PIN 2   // On-board LED is usually GPIO2

/*
middleware -> esp32
{
  "command": "set_motor_power",
  "parameters": {
    "L":int(0-255)
    "R":int(0-255)
  }
}

{
  "command": "set_motor_PID",
  "parameters": {
    "Kp":float,
    "Ki":float,
    "Kd":float
  }
}

//24 is rpm limit of the motor
{
  "command": "set_motor_rpm",
  "parameters": {
    "L":float(0-24),
    "R":float(0-24),
  }
}

esp32 -> middleware
{
  "feedback_type": "motor_rpm",
  "data":{
    "L":float
    "R":float
  }
}

{
  "feedback_type": "debug_msg",
  "data":{
    "msg":str
  }
}
*/

void process_received_json_to_control(String& jsonString){
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, jsonString);
  if(error){
    String error_str="JSON parse failed: ";
    error_str+=error.c_str();
    send_serial_debug_msg_feedback(error_str);
  }
  
  const char* command = doc["command"];
  if(strcmp(command, "set_motor_power")==0){
    int L=doc["parameters"]["L"];
    int R=doc["parameters"]["R"];
    setMotorPower(L, R);
    send_serial_debug_msg_feedback("Motor power updated");
  }
  else if(strcmp(command, "set_motor_PID")==0){
    float new_Kp = doc["parameters"]["Kp"];
    float new_Ki = doc["parameters"]["Ki"];
    float new_Kd = doc["paramteres"]["Kd"];
    setMotorPID(new_Kp,new_Ki,new_Kd);
    send_serial_debug_msg_feedback("Motor PID updated");
  }
  else if(strcmp(command, "set_motor_rpm")==0){
    float L=doc["parameters"]["L"];
    float R=doc["parameters"]["R"];

    setMotorRPM(L,R);
    send_serial_debug_msg_feedback("Motor RPM updated");
  }
  else{
    send_serial_debug_msg_feedback("Unknown command detected");
  }
}


TaskHandle_t task_receive_serial_handle = NULL;

void task_receive_serial(void *pvParameters){
  while(true){
    static String input="";
    while(Serial.available()){
      char c=(char)Serial.read();
      if(c=='\n'){
        process_received_json_to_control(input);
      }else{
        input+=c;
      }
    }
  }
}


void setup_serial_comm_and_control(){
  xTaskCreate(
    task_receive_serial,
    "task_receive_serial function runner",
    4096,
    NULL,
    1,
    &task_receive_serial_handle
  );
}


void setup() {
  Serial.begin(115200);
  // Set pin as output
  pinMode(LED_PIN, OUTPUT);

  setup_pin_for_L298N();
  setup_pin_for_motor_spd_encoding();
  setup_serial_comm_and_control();

}
  
void loop() {
  
}
