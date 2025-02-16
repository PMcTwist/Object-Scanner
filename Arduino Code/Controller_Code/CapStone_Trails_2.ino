// #include <AccelStepper.h>
// #include <AccelStepperWithDistance.h>

// #define Y_STEP_PIN 3
// #define Y_DIR_PIN 6
// #define Y_ENABLE_PIN 8

// AccelStepperWithDistance stepperY(AccelStepperWithDistance::DRIVER, Y_STEP_PIN, Y_DIR_PIN);

// void setup() {
//   Serial.begin(115200);
  
//   stepperY.setMaxSpeed(1000);
//   stepperY.setAcceleration(500);
//   stepperY.setStepsPerRotation(200);   // 1.8° stepper motor
//   stepperY.setMicroStep(16);           // 1/16 microstepping
//   stepperY.setDistancePerRotation(8);  // 8mm per rotation
//   stepperY.setAnglePerRotation(360);   // Standard 360° per rotation
  
//   // Move to 50mm
//   stepperY.runToNewDistance(50);
//   Serial.print("Current position: ");
//   Serial.println(stepperY.getCurrentPositionDistance());
  
//   // Move relatively by -20mm
//   stepperY.runRelative(-20);
//   Serial.print("New position after relative move: ");
//   Serial.println(stepperY.getCurrentPositionDistance());
  
//   // Move to 90° angle
//   stepperY.runToNewAngle(90);
//   Serial.print("Position after moving to 90°: ");
//   Serial.println(stepperY.getCurrentPositionDistance());
  
//   // Set up a move to 100mm (but don't execute it yet)
//   stepperY.moveToDistance(100);
// }

// void loop() {
//   // Execute the move set up in setup()
//   if (stepperY.distanceToGo() != 0) {
//     stepperY.run();
//   }
// }