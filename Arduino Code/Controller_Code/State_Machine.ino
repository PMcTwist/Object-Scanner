#include <Arduino.h>
#include <Wire.h>
#include <TFLI2C.h>


// ===== LiDAR Sensor =====
TFLI2C tflI2C;
int16_t tfDist;
int16_t tfAddr = TFL_DEF_ADR;

// ==== Micro-Step Jumper =====
const int micro_jumper = 4; // 4 is for 1/4 microsteps

// ===== Platform Geometry =====
const float y_StepAngle = 1.8;
const float platformRadius = 100; // mm
const float stepsPerRev = (360 / y_StepAngle) * micro_jumper; 
const float platformCircumference = 2.0 * 3.1415926535 * platformRadius;
const float y_DistancePerStep = platformCircumference / stepsPerRev;

// ===== Threaded Rod Geometry =====
const float rodPitch = 2; // mm
const float z_stepsPerRev = 200 * micro_jumper; // 200 steps/rev for NEMA 17
const float z_DistancePerStep = rodPitch / z_stepsPerRev;

// ===== Stepper Pins & Setup =====
#define ENABLE_PIN 8

#define Y_STEP_PIN 3
#define Y_DIR_PIN 6

#define Z_STEP_PIN 4
#define Z_DIR_PIN 7
 
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
const unsigned long homingTimeout = 1000000000;

// 3 measured distances
float x_dist = 0.0;
float y_axis_total_distance = 0.0;
float z_axis_total_distance = 0.0;

// Array of send data
int dataArray[3];

int yStepCount = 0;
int zStepCount = 0;

const int yStepsPerZ = 200 * micro_jumper;
const int zStepsTotal = 200 * micro_jumper;
 
// Step timing variables
unsigned long lastHomingStepTime = 0;
const unsigned long homingStepInterval = 1000; // 10ms between homing steps (much slower)
 
// Custom stepper functions (much slower timing)
void stepY(int direction) {
  digitalWrite(Y_DIR_PIN, direction > 0 ? HIGH : LOW);
  delayMicroseconds(10); // Let direction settle
  digitalWrite(Y_STEP_PIN, HIGH);
  delayMicroseconds(5);
  digitalWrite(Y_STEP_PIN, LOW);
  delayMicroseconds(1000); // Pause between steps
}
 
void stepZ(int direction) {
  digitalWrite(Z_DIR_PIN, direction > 0 ? HIGH : LOW);
  delayMicroseconds(10); // Let direction settle  
  digitalWrite(Z_STEP_PIN, HIGH);
  delayMicroseconds(5);
  digitalWrite(Z_STEP_PIN, LOW);
  delayMicroseconds(1000); // Pause between steps
}
 
void stepZHoming() {
  // Non-blocking homing step
  if (micros() - lastHomingStepTime >= homingStepInterval) {
    digitalWrite(Z_DIR_PIN, LOW); // Move down for homing
    digitalWrite(Z_STEP_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(Z_STEP_PIN, LOW);
    lastHomingStepTime = micros();
  }
}
 
// Setup loop to define parameters
void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW); // Enable steppers
  
  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  
  pinMode(Z_STEP_PIN, OUTPUT);
  pinMode(Z_DIR_PIN, OUTPUT);
 
  pinMode(limitSwitchBot, INPUT_PULLUP);
  pinMode(limitSwitchTop, INPUT_PULLUP);
  
  Serial.println("Ready!");
}

// ===== Main Loop =====
// This loop runs the state machine for the scanning process
void loop() {
  // Event Listener for UI
  if (Serial.available() > 0) {
    char inputChar = Serial.read() & 0x7F;
    Serial.print("Received: ");
    Serial.println(inputChar);
   
    if (inputChar == '1') {
      if (!running) {
        Serial.println("Starting Scan");
        scanState = HOMING;
        running = true;
        stopFlag = false;
      }
    } else if (inputChar == '0') {
      if (running) {
        Serial.println("Stopping Scan");
        scanState = DONE;
      }
    }
  }
  
  // State Machine Case Structure
  switch (scanState) {
    // Wait for instructions
    case IDLE:
      break;
    
    // Homes the Z axis to the 0 point to start
    case HOMING:
      if (!homingStarted) {
        Serial.println("Homing Z Axis...");
        homingStartTime = millis();
        homingStarted = true;
        lastHomingStepTime = 0;
      }
      // Check if limit switch is still open (not triggered)
      if (digitalRead(limitSwitchBot) == HIGH) {
        // Take homing steps
        stepZHoming();
        // Check for timeout
        if (millis() - homingStartTime > homingTimeout) {
          Serial.println("Homing timeout: switch not triggered.");
          homingComplete = false;
          running = false;
          stopFlag = true;
          homingStarted = false;
          scanState = IDLE;
        }
      } else {
        // Limit switch triggered - homing complete
        Serial.println("Z axis homed successfully.");
        homingComplete = true;
        homingStarted = false;
        scanState = START_SCAN;
      }
      break;
    
    // Initialize scan parameters
    case START_SCAN:
      Serial.println("Initializing scan...");
      yStepCount = 0;
      zStepCount = 0;
      y_axis_total_distance = 0;
      z_axis_total_distance = 0;
      scanState = MOVE_Y;
      break;

    // Move Y motor for platform rotation and take measurements
    case MOVE_Y:
      if (yStepCount < yStepsPerZ) {
        // Take a Y step
        stepY(1);
        y_axis_total_distance += y_DistancePerStep;
        yStepCount++;

        // Take LiDAR measurement
        if (tflI2C.getData(tfDist, tfAddr)) {
          x_dist = tfDist * 10; // Convert to mm
        } else {
          x_dist = 0; // Default if measurement fails
        }

        // Prepare data
        dataArray[0] = (int)x_dist;
        dataArray[1] = (int)y_axis_total_distance;
        dataArray[2] = (int)z_axis_total_distance;

        // Send data
        String dataToSend = String("DATA(") + String(dataArray[0]) + "," + String(dataArray[1]) + "," + String(dataArray[2]) + String(")");
        Serial.println(dataToSend);

        // Small delay between measurements
        delay(200); // Longer delay between Y steps
      } else {
        // Completed all Y steps for this Z level
        if (zStepCount >= zStepsTotal) {
          // Completed entire scan
          scanState = DONE;
        } else {
          // Move to next Z level
          scanState = MOVE_Z;
        }
      }
      break;
    
    // Move Z axis up one step
    case MOVE_Z:
      Serial.print("Moving Z axis up - step ");
      Serial.println(zStepCount + 1);

      for (int i = 0; i < z_stepsPerRev; i++) {
        stepZ(1); // Move Z one microstep
      }

      // Z moved 1 full rotation (2mm)
      z_axis_total_distance += rodPitch; // 2mm per full thread revolution
      zStepCount++;

      // Reset Y parameters for this Z level
      yStepCount = 0;
      y_axis_total_distance = 0.0;
      scanState = MOVE_Y;
      break;
    
    // Complete state
    case DONE:
      if (digitalRead(limitSwitchTop) == LOW) {
        Serial.println("Top limit reached. Stopping scan.");
      } else {
        Serial.println("Scan completed successfully.");
      }
      homingComplete = false;
      running = false;
      stopFlag = true;
      scanState = IDLE;
      break;
  }
  // Small delay to prevent overwhelming the system
  delay(1);
}