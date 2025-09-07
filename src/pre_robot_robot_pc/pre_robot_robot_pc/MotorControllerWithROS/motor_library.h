// L298N config for left side motor
#define ENB 19
#define IN4 18
#define IN3 5

// L298N config for right side motor
#define IN2 17
#define IN1 16
#define ENA 4

void setMotorPower(int motorL, int motorR) {
  // motorL and motorR range: -255 .. 255
  // negative = backward, positive = forward, 0 = stop

  // --- Left Motor ---
  if (motorL > 0) {
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    ledcWrite(ENB, motorL);   // channel 0 for ENB
  } else if (motorL < 0) {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    ledcWrite(ENB, -motorL);  // take absolute value
  } else {
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    ledcWrite(ENB, 0);
  }

  // --- Right Motor ---
  if (motorR > 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    ledcWrite(ENA, motorR);   // channel 1 for ENA
  } else if (motorR < 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    ledcWrite(ENA, -motorR);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    ledcWrite(ENA, 0);
  }
}

void setup_pin_for_L298N() {
  // Motor pins
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  ledcAttachChannel(ENB, 20000, 8, 0);
  ledcAttachChannel(ENA, 20000, 8, 1);

  // Configure PWM for ENA and ENB
  // ledcSetup(0, 1000, 8); // channel 0, 1kHz, 8-bit resolution
  // ledcAttachPin(ENB, 0); // left motor enable pin to channel 0
  // ledcSetup(1, 1000, 8); // channel 1, 1kHz, 8-bit resolution
  // ledcAttachPin(ENA, 1); // right motor enable pin to channel 1
}


//Motor speed reading involve


const int PPR = 2950;

#define LEFT_C1 13
#define LEFT_C2 12
#define LEFT_encoderA 13
#define LEFT_encoderB 12

volatile long left_encoder_count = 0;
unsigned long left_lastTime = 0;
float left_motorRPM = 0.0;


void IRAM_ATTR left_encoderISR(){
  if (digitalRead(LEFT_encoderB)==HIGH){
    left_encoder_count+=1;
  }else{
    left_encoder_count-=1;
  }
}


#define RIGHT_C1 14
#define RIGHT_C2 27
#define RIGHT_encoderA 14
#define RIGHT_encoderB 27

volatile long right_encoder_count = 0;
unsigned long right_lastTime = 0;
float right_motorRPM = 0.0;

void IRAM_ATTR right_encoderISR(){
  if (digitalRead(RIGHT_encoderB)==HIGH){
    right_encoder_count-=1;
  }else{
    right_encoder_count+=1;
  }
}

TaskHandle_t task_update_motor_RPM_handle = NULL;

bool motor_with_PID = false;
// float Kp = 0.5;
// float Ki = 0.2;
// float Kd = 0.1;

float Kp = 20;
float Ki = 3;
float Kd = 3;

float target_motorRPM_L = 0.0;
float target_motorRPM_R = 0.0;

float prev_error_L = 0;
float integral_L = 0;
float prev_error_R = 0;
float integral_R = 0;

void task_update_motor_RPM(void *pvParameters){
  while(true){
    unsigned long currentTime = millis();
    unsigned long dt = currentTime - left_lastTime;

    if(dt>=100){//calculate every 100ms
      //Calculate speed in rpm
      long left_count;
      long right_count;
      noInterrupts();
      left_count = left_encoder_count;
      left_encoder_count=0;
      right_count = right_encoder_count;
      right_encoder_count=0;
      interrupts();

      left_motorRPM = (left_count/(float)PPR) * (60000.0 / dt);
      right_motorRPM = (right_count/(float)PPR) * (60000.0 / dt);




      if(motor_with_PID==true){
        float error_L = target_motorRPM_L - left_motorRPM;
        integral_L += error_L;
        float derivative_L = error_L - prev_error_L;
        int output_L = (Kp * error_L) + (Ki * integral_L) + (Kd * derivative_L);

        float error_R = target_motorRPM_R - right_motorRPM;
        integral_R += error_R;
        float derivative_R = error_R - prev_error_R;
        int output_R = (Kp * error_R) + (Ki * integral_R) + (Kd * derivative_R);


        prev_error_L = error_L;
        prev_error_R = error_R;

        output_L = constrain(output_L, -255,255);
        output_R = constrain(output_R, -255,255);
        setMotorPower(output_L,output_R);

        Serial.printf("Target %.2f %.2f | Current %.2f %.2f | Output %d %d\n", 
                      target_motorRPM_L, target_motorRPM_R, 
                      left_motorRPM, right_motorRPM, 
                      output_L, output_R);

      }else{
        Serial.print("Motor RPM: ");
        Serial.print(left_motorRPM);
        Serial.print(" ");
        Serial.println(right_motorRPM);
      }

      left_lastTime = currentTime;
      right_lastTime = currentTime;
    }
  }
}

void setup_pin_for_motor_spd_encoding(){
  pinMode(LEFT_encoderA, INPUT);
  pinMode(LEFT_encoderB, INPUT);
  attachInterrupt(digitalPinToInterrupt(LEFT_encoderA),left_encoderISR, RISING);
  pinMode(RIGHT_encoderA, INPUT);
  pinMode(RIGHT_encoderB, INPUT);
  attachInterrupt(digitalPinToInterrupt(RIGHT_encoderA),right_encoderISR, RISING);
  left_lastTime=millis();
  right_lastTime=millis();


  xTaskCreate(
    task_update_motor_RPM,
    "Motor speed publisher",
    4096,
    NULL,
    1,
    &task_update_motor_RPM_handle
  );
}

