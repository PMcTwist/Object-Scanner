#include <Arduino.h>
#include <Wire.h>
#include <TFLI2C.h>
#include <AccelStepper.h>

// ===== LiDAR Sensor =====
TFLI2C tflI2C;
int16_t tfDist;
int16_t tfAddr = TFL_DEF_ADR;

// ===== Platform Geometry =====
const float y_StepAngle = 1.8;
const float platformRadius = 100; // mm
const float stepsPerRev = 360 / y_StepAngle;
const float platformCircumference = 2.0 * 3.1415926535 * platformRadius;
const float y_DistancePerStep = platformCircumference / stepsPerRev;

// ===== Threaded Rod Geometry =====
const float rodPitch = 2; // mm
const float z_DistancePerStep = rodPitch / stepsPerRev;

// ===== Stepper Pins & Setup =====
#define ENABLE_PIN 8
#define Y_STEP_PIN 3
#define Y_DIR_PIN 6
#define Z_STEP_PIN 4
#define Z_DIR_PIN 7

AccelStepper stepperY(1, Y_STEP_PIN, Y_DIR_PIN);
AccelStepper stepperZ(1, Z_STEP_PIN, Z_DIR_PIN);

#define limitSwitchTop 11
#define limitSwitchBot 10

// ===== Scan State Machine =====
enum ScanState {
  IDLE,
  HOMING,
  START_SCAN,
  MOVE_Z,
  MOVE_Y,
  RECORD_DATA,
  DONE
};
ScanState scanState = IDLE;

// ===== Motion & Scan Variables =====
// Status flags
bool homingComplete = false;
bool running = false;
bool stopFlag = true;

bool homingStarted = false;
unsigned long homingStartTime = 0;
const unsigned long homingTimeout = 10000;

// 3 measured distances
float x_dist = 0.0;
float y_axis_total_distance = 0.0;
float z_axis_total_distance = 0.0;

// Array of send data
int dataArray[3];

int yStepCount = 0;
int zStepCount = 0;
const int yStepsPerZ = 200;
const int zStepsTotal = 200;
bool stepIssuedY = false;
bool stepIssuedZ = false;


// Setup loop to define parameters
void setup() {
  Serial.begin(115200);
  Wire.begin();

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);

  pinMode(limitSwitchBot, INPUT_PULLUP);
  pinMode(limitSwitchTop, INPUT_PULLUP);

  stepperY.setMaxSpeed(200);
  stepperZ.setMaxSpeed(200);

  Serial.println("Ready!");
}


// Run-Time loop to hold state machine
void loop() {
  // Event Listener for UI
  if (Serial.available() > 0) {
    char inputChar = Serial.read() & 0x7F;
    Serial.print("Received: ");
    Serial.println(inputChar);

    if (inputChar == '1') {
      if (!running) {
        scanState = HOMING;
      }
    } else if (inputChar == '0') {
      if (running) {
        scanState = DONE;
      }
    }
  }

  // State Machine Case Structure
  switch (scanState) {
    // Spin goto spin...to wait for instructions
    case IDLE:
      break;

    // Homes the Z axis to the 0 point to start
    case HOMING:
      if (!homingStarted) {
        Serial.println("Homing Z Axis...");
        digitalWrite(ENABLE_PIN, LOW);
        stepperZ.setMaxSpeed(300);
        stepperZ.setAcceleration(100);
        stepperZ.setSpeed(-200);  // Adjust direction if needed
        homingStartTime = millis();
        homingStarted = true;
      }

      if (digitalRead(limitSwitchBot) == HIGH) {
        Serial.println("Made it to stepper run!");
        stepperZ.runSpeed();  // Must be called frequently!
        if (millis() - homingStartTime > homingTimeout) {
          Serial.println("Homing timeout: switch not triggered.");
          homingComplete = false;
          running = false;
          stopFlag = true;
          homingStarted = false;
          scanState = IDLE;
        }
      } else {
        stepperZ.stop();  // stops movement smoothly
        stepperZ.setCurrentPosition(0);
        Serial.println("Z axis homed.");
        homingComplete = true;
        homingStarted = false;
        scanState = START_SCAN;
      }
      break;

    // Starts the over all scan by moving y and then z
    case START_SCAN:
      yStepCount = 0;
      zStepCount = 0;
      y_axis_total_distance = 0;
      z_axis_total_distance = 0;
      stepperY.setCurrentPosition(0);
      stepperZ.setCurrentPosition(0);
      scanState = MOVE_Z;
      break;

    case MOVE_Z:
      if (!stepIssuedZ) {
        stepperZ.move(1);
        z_axis_total_distance += z_DistancePerStep;
        stepIssuedZ = true;
      }
      stepperZ.run();
      if (stepperZ.distanceToGo() == 0 && stepIssuedZ) {
        stepIssuedZ = false;
        yStepCount = 0;
        scanState = MOVE_Y;
      }
      break;

    // Moves Y motor for platform
    case MOVE_Y:
      if (!stepIssuedY && yStepCount < yStepsPerZ) {
        stepperY.move(1);
        y_axis_total_distance += y_DistancePerStep;
        stepIssuedY = true;
      }
      stepperY.run();
      if (stepperY.distanceToGo() == 0 && stepIssuedY) {
        stepIssuedY = false;
        yStepCount++;

        if (tflI2C.getData(tfDist, tfAddr)) {
          x_dist = tfDist * 10;
        }

        dataArray[0] = x_dist;
        dataArray[1] = y_axis_total_distance;
        dataArray[2] = z_axis_total_distance;

        // Build serial packet
        String dataToSend = String(dataArray[0]) + "," + String(dataArray[1]) + "," + String(dataArray[2]);

        // Send serial packet
        Serial.println(dataToSend);
      }
      if (yStepCount >= yStepsPerZ) {
        scanState = ++zStepCount >= zStepsTotal ? DONE : MOVE_Z;
      }
      break;

    // Complete state...one way or another...
    case DONE:
      if (digitalRead(limitSwitchTop) == LOW) {
        Serial.println("Top limit reached. Stopping scan.");
      } else {
        Serial.println("Scanning Stopped.");
      }
      homingComplete = false;
      running = false;
      stopFlag = true;
      scanState = IDLE;
      break;
  }
  // Drags it's feet to catch up
  delay(1);
}
