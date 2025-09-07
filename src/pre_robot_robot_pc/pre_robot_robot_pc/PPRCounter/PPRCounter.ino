const int encoderPinA = 13;  // Connect C1 to GPIO 18
const int encoderPinB = 12;  // Connect C2 to GPIO 19

volatile long pulseCount = 0;

void IRAM_ATTR encoderISR() {
  pulseCount++;  // count every pulse
}

void setup() {
  Serial.begin(115200);

  pinMode(encoderPinA, INPUT);
  pinMode(encoderPinB, INPUT);

  attachInterrupt(digitalPinToInterrupt(encoderPinA), encoderISR, RISING);

  Serial.println("Rotate the motor exactly one full revolution...");
  Serial.println("Counting pulses...");
}

void loop() {
  // Print current pulse count every second
  static unsigned long lastPrint = 0;
  unsigned long now = millis();
  if (now - lastPrint >= 1000) {
    noInterrupts();
    long count = pulseCount;
    interrupts();

    Serial.print("Pulses counted so far: ");
    Serial.println(count);

    lastPrint = now;
  }
}
