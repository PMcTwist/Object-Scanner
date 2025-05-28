#include <AccelStepper.h>

#define Z_STEP_PIN 4
#define Z_DIR_PIN 7
#define ENABLE_PIN 8

AccelStepper stepperZ(AccelStepper::DRIVER, Z_STEP_PIN, Z_DIR_PIN);

void setup() {
  Serial.begin(115200);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);  // ENABLE motors

  stepperZ.setMaxSpeed(400);
  stepperZ.setAcceleration(100);
  stepperZ.setSpeed(-200);  // Flip sign if needed
}

void loop() {
  stepperZ.runSpeed();
}
