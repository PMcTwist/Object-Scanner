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
  START_SCAN,
  MOVE_Z,
  MOVE_Y,
  RECORD_DATA,
  DONE
};
ScanState scanState = IDLE;

// ===== Motion & Scan Variables =====
// Status flags
bool running = false;
bool stopFlag = true;

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

void loop() {
  checkForUpdates();
  checkDone();

  switch (scanState) {
    case IDLE:
      break;

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
        String dataToSend = String(dataArray[0]) + "," + String(dataArray[1]) + "," + String(dataArray[2]);
        Serial.println(dataToSend);
      }
      if (yStepCount >= yStepsPerZ) {
        scanState = ++zStepCount >= zStepsTotal ? DONE : MOVE_Z;
      }
      break;

    case DONE:
      running = false;
      stopFlag = true;
      Serial.println("Scan complete.");
      checkHome();
      scanState = IDLE;
      break;
  }
  delay(1);
}

void checkForUpdates() {
  if (Serial.available() > 0) {
    char inputChar = Serial.read() & 0x7F;
    Serial.print("Received: ");
    Serial.println(inputChar);

    if (inputChar == '1') {
      if (!running) {
        running = true;
        stopFlag = false;
        scanState = START_SCAN;
        Serial.println("Scanning...");
      }
    } else if (inputChar == '0') {
      if (running) {
        running = false;
        stopFlag = true;
        scanState = IDLE;
        Serial.println("Scanning Stopped");
        checkHome();
      }
    }
  }
}

void checkDone() {
  if (digitalRead(limitSwitchTop) == LOW) {
    Serial.println("Top limit reached. Stopping scan.");
    running = false;
    stopFlag = true;
    scanState = IDLE;
    checkHome();
  }
}

// void checkHome() {
//   Serial.println("Homing Z Axis...");

//   // Ensure driver is enabled
//   digitalWrite(ENABLE_PIN, LOW);

//   // Direction toward home (adjust sign if needed)
//   stepperZ.setMaxSpeed(300);
//   stepperZ.setAcceleration(100);
//   stepperZ.setSpeed(-200);  // Try +200 if direction is wrong

//   unsigned long startTime = millis();
//   const unsigned long timeout = 10000; // 10 sec timeout

//   while (digitalRead(limitSwitchBot) == HIGH) {
//     stepperZ.runSpeed();  // runSpeed ignores acceleration
//     if (millis() - startTime > timeout) {
//       Serial.println("Homing timeout: switch not triggered.");
//       break;
//     }
//   }

//   stepperZ.stop();  // ensures it's not moving
//   stepperZ.setCurrentPosition(0);  // reset position to 0
//   Serial.println("Z axis homed.");
// }

bool homeZAxis() {
  static bool started = false;

  if (!started) {
    Serial.println("Starting homing...");
    stepperZ.setMaxSpeed(300);
    stepperZ.setAcceleration(100);
    stepperZ.setSpeed(-200);
    started = true;
  }

  if (digitalRead(limitSwitchBot) == HIGH) {
    stepperZ.runSpeed();
    return false; // still homing
  } else {
    stepperZ.stop();
    stepperZ.setCurrentPosition(0);
    Serial.println("Z homing complete.");
    started = false; // reset for next call
    return true;     // homing done
  }
}