// TEST 1

// #include <AccelStepper.h>

// #define Z_STEP_PIN 4
// #define Z_DIR_PIN 7
// #define ENABLE_PIN 8

// AccelStepper stepperZ(AccelStepper::DRIVER, Z_STEP_PIN, Z_DIR_PIN);

// void setup() {
//   Serial.begin(115200);
//   pinMode(ENABLE_PIN, OUTPUT);
//   digitalWrite(ENABLE_PIN, LOW);  // ENABLE motors

//   stepperZ.setMaxSpeed(400);
//   stepperZ.setAcceleration(100);
//   stepperZ.setSpeed(-200);  // Flip sign if needed
// }

// void loop() {
//   Serial.print("Trying to Step Z... ");
//   stepperZ.runSpeed();
// }

// TEST 2

// #include <Arduino.h>
 
// // ===== Stepper Pins =====
// #define ENABLE_PIN 8
// #define Y_STEP_PIN 3
// #define Y_DIR_PIN 6
// #define Z_STEP_PIN 4
// #define Z_DIR_PIN 7
 
// void setup() {
//   Serial.begin(115200);
//   // Set up pins
//   pinMode(ENABLE_PIN, OUTPUT);
//   pinMode(Y_STEP_PIN, OUTPUT);
//   pinMode(Y_DIR_PIN, OUTPUT);
//   pinMode(Z_STEP_PIN, OUTPUT);
//   pinMode(Z_DIR_PIN, OUTPUT);
//   // Enable the stepper drivers
//   digitalWrite(ENABLE_PIN, LOW);  // Try LOW first
//   Serial.println("Manual Stepper Test Starting...");
//   Serial.println("Testing Y motor first, then Z motor");
//   delay(2000); // Wait for driver to initialize
// }
 
// void loop() {
//   Serial.println("Testing Y Motor - 10 steps clockwise");
//   // Set direction
//   digitalWrite(Y_DIR_PIN, HIGH);
//   delay(100); // Let direction settle
//   // Take 10 slow steps
//   for(int i = 0; i < 10; i++) {
//     digitalWrite(Y_STEP_PIN, HIGH);
//     delay(100);  // Very slow for testing
//     digitalWrite(Y_STEP_PIN, LOW);
//     delay(100);
//     Serial.print("Y Step: ");
//     Serial.println(i + 1);
//   }
//   delay(2000); // Pause between tests
//   Serial.println("Testing Y Motor - 10 steps counterclockwise");
//   // Change direction
//   digitalWrite(Y_DIR_PIN, LOW);
//   delay(100);
//   // Take 10 slow steps
//   for(int i = 0; i < 10; i++) {
//     digitalWrite(Y_STEP_PIN, HIGH);
//     delay(100);
//     digitalWrite(Y_STEP_PIN, LOW);
//     delay(100);
//     Serial.print("Y Step: ");
//     Serial.println(i + 1);
//   }
//   delay(2000);
//   Serial.println("Testing Z Motor - 10 steps up");
//   // Set direction
//   digitalWrite(Z_DIR_PIN, HIGH);
//   delay(100);
//   // Take 10 slow steps
//   for(int i = 0; i < 10; i++) {
//     digitalWrite(Z_STEP_PIN, HIGH);
//     delay(100);
//     digitalWrite(Z_STEP_PIN, LOW);
//     delay(100);
//     Serial.print("Z Step: ");
//     Serial.println(i + 1);
//   }
//   delay(2000);
//   Serial.println("Testing Z Motor - 10 steps down");
//   // Change direction
//   digitalWrite(Z_DIR_PIN, LOW);
//   delay(100);
//   // Take 10 slow steps
//   for(int i = 0; i < 10; i++) {
//     digitalWrite(Z_STEP_PIN, HIGH);
//     delay(100);
//     digitalWrite(Z_STEP_PIN, LOW);
//     delay(100);
//     Serial.print("Z Step: ");
//     Serial.println(i + 1);
//   }
//   delay(5000); // Long pause before repeating
//   Serial.println("--- Test Complete - Repeating ---");
// }

// TEST 3

#include <Arduino.h>

// Define Z Axis pins (from original code)
#define ENABLE_PIN 8
#define Z_STEP_PIN 4
#define Z_DIR_PIN 7

void setup() {
  // Serial optional
  Serial.begin(115200);
  Serial.println("Z Axis Test Starting...");

  // Stepper driver setup
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW); // Enable stepper driver (Active LOW)

  pinMode(Z_STEP_PIN, OUTPUT);
  pinMode(Z_DIR_PIN, OUTPUT);

  // Set direction to "UP"
  digitalWrite(Z_DIR_PIN, HIGH);
}

void loop() {
  // Single step pulse
  digitalWrite(Z_STEP_PIN, HIGH);
  delay(10); // 10ms HIGH pulse
  digitalWrite(Z_STEP_PIN, LOW);
  delay(1000); // 1 second delay between steps (slow visible stepping)

  Serial.println("Step Z");
}
