#include <Arduino.h>

// ===== Sharp IR Sensor =====
#define SENSOR_PIN A0
int scan_amount = 40;  // Number of readings to average

// distance of sensor from middle of platform
const float distance_to_center = 150.0; // mm - adjust this to your actual setup

// ==== Full Step Configuration =====
const int micro_jumper = 2; // 2 is for 1/2 microstepping

// ===== Scan Parameters =====
// Reduce the scans per step to help scan time
const int stepsPerReading = 1;  // Take a reading every single step - no more multiple steps!

// ===== Platform Geometry =====
const float y_StepAngle = 1.8; // degrees per full step
const int motor_steps_per_rev = 360 / y_StepAngle; // 200 for 1.8°
const int stepsPerRev = motor_steps_per_rev * micro_jumper; // 200 * 2 = 400 for 1/2 steps
const float platformRadius = 100; // mm
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
bool foundValidPoint = false;

// data send timer
unsigned long lastDataSendTimer = 0;
const unsigned long dataSendInterval = 50; // Reduced from 100ms to 50ms

// Homing variables
unsigned long homingStartTime = 0;
const unsigned long homingTimeout = 1000000000;

// 3 measured distances
float x_dist = 0.0;
float y_axis_total_distance = 0.0;
float z_axis_total_distance = 0.0;

// Array of send data
float dataArray[3];

int yStepCount = 0;
int zStepCount = 0;

const int yStepsPerZ = stepsPerRev; 
const int zStepsTotal = 200 * micro_jumper;
 
// Step timing variables
unsigned long lastHomingStepTime = 0;
const unsigned long homingStepInterval = 800; // Reduced from 1000 to 800 microseconds
 
// Faster 1/2 microstepping reliable stepping functions
void stepY(int direction) {
  // Set direction and wait
  digitalWrite(Y_DIR_PIN, direction > 0 ? HIGH : LOW);
  delayMicroseconds(500); // Reduced from 2ms to 500µs
  
  // Create step pulse
  digitalWrite(Y_STEP_PIN, HIGH);
  delayMicroseconds(200); // Reduced from 300µs to 200µs
  digitalWrite(Y_STEP_PIN, LOW);
  
  // Delay between steps - significantly reduced for speed
  delay(50); // Reduced from 100ms to 50ms
}
 
void stepZ(int direction) {
  digitalWrite(Z_DIR_PIN, direction > 0 ? HIGH : LOW);
  delayMicroseconds(300); // Reduced from 500µs
  digitalWrite(Z_STEP_PIN, HIGH);
  delayMicroseconds(80); // Reduced from 100µs
  digitalWrite(Z_STEP_PIN, LOW);
  delay(3); // Reduced from 5ms to 3ms
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

// Sharp IR sensor reading function (returns distance in cm)
float readSensor(int samples = 40) {
  float analog_total = 0;
  float measured_analog = 0;

  for (int i = 0; i < samples; i++) {
    measured_analog = analogRead(SENSOR_PIN);
    analog_total += measured_analog;
    delay(2);  // Small delay between readings
  }

  float distance = analog_total / samples;  // Get the mean
  
  // Convert analog reading to voltage (assuming 5V reference)
  distance = (distance * 5.0) / 1023.0;
  
  // Sharp GP2Y0A51SK0F formula from datasheet (distance in cm)
  distance = -5.40274*pow(distance,3) + 28.4823*pow(distance,2) - 49.7115*distance + 31.3444;
  
  return distance;  // Return distance in cm
}

// Helper function for float mapping
float mapFloat(float fval, float val_in_min, float val_in_max, float val_out_min, float val_out_max) {
  return (fval - val_in_min) * (val_out_max - val_out_min) / (val_in_max - val_in_min) + val_out_min;
}
 
// Setup loop to define parameters
void setup() {
  Serial.begin(115200);
  
  pinMode(SENSOR_PIN, INPUT);
  analogReference(DEFAULT);  // Use 5V reference for Sharp sensor
  
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, HIGH); // Enable steppers
  
  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  
  pinMode(Z_STEP_PIN, OUTPUT);
  pinMode(Z_DIR_PIN, OUTPUT);
 
  pinMode(limitSwitchBot, INPUT_PULLUP);
  pinMode(limitSwitchTop, INPUT_PULLUP);
  
  Serial.println("STAT(Ready with Sharp IR sensor!)");
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
        Serial.println("STAT(Starting Scan)");
        scanState = HOMING;
        running = true;
        stopFlag = false;
      }
    } else if (inputChar == '0') {
      if (running) {
        Serial.println("STAT(Stopping Scan)");
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
      digitalWrite(ENABLE_PIN, LOW); // Enable steppers for homing
      if (!homingStarted) {
        Serial.println("STAT(Homing Z Axis...)");
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
          Serial.println("STAT(Homing timeout: switch not triggered.)");
          homingComplete = false;
          running = false;
          stopFlag = true;
          homingStarted = false;
          scanState = IDLE;
        }
      } else {
        // Limit switch triggered - homing complete
        Serial.println("STAT(Z axis homed successfully.)");
        homingComplete = true;
        homingStarted = false;
        scanState = START_SCAN;
      }
      break;
    
    // Initialize scan parameters
    case START_SCAN:
      Serial.println("STAT(Scanning...)");
      yStepCount = 0;
      zStepCount = 0;
      y_axis_total_distance = 0;
      z_axis_total_distance = 0;
      scanState = MOVE_Y;
      break;

    // Move Y motor for platform rotation and take measurements
    case MOVE_Y:
      if (yStepCount < yStepsPerZ) {
        Serial.println("STAT(Scanning...)");

        // Calculate current angle BEFORE taking measurement (this is the current position)
        float angle = (yStepCount * 2.0 * PI) / stepsPerRev;

        // reset point flag
        foundValidPoint = false;

        // Take averaged Sharp IR measurement (in cm)
        x_dist = readSensor(40);

        // Convert distance to mm and apply the working formula from reference code
        float measured_distance_mm = x_dist * 10; // Convert cm to mm
        float distance_from_center = distance_to_center - measured_distance_mm;

        // Check if the measurement is valid (object is between sensor and center)
        if (distance_from_center > 0 && distance_from_center <= (platformRadius * 2)) {
          // Scanned point is valid
          foundValidPoint = true;

          // Calculate Cartesian coordinates using the working formula
          float x = sin(angle) * distance_from_center;  // Note: sin for X
          float y = cos(angle) * distance_from_center;  // Note: cos for Y
          float z = z_axis_total_distance;

          // Prepare data
          dataArray[0] = x;
          dataArray[1] = y;
          dataArray[2] = z;

          // Send data with throttled timing applied (now faster)
          if (millis() - lastDataSendTimer >= dataSendInterval) {
            String dataToSend = String("DATA(") + String(dataArray[0]) + "," + String(dataArray[1]) + "," + String(dataArray[2]) + String(")");
            Serial.println(dataToSend);
            lastDataSendTimer = millis();
          }
        }

        // NOW move to next position AFTER taking the measurement
        for (int i = 0; i < stepsPerReading; i++) {
            stepY(1);
            y_axis_total_distance += y_DistancePerStep;
            yStepCount++;
            
            // Check if we've reached the total steps
            if (yStepCount >= yStepsPerZ) {
                break;
            }
        }
        
        // Faster delay between measurements
        delay(100); // Reduced from 200ms to 100ms
      } else {
        // Completed all Y steps for this Z level
        if (!foundValidPoint) {
          // Completed entire scan
          scanState = DONE;
        } else {
          // Move to next Z level
          scanState = MOVE_Z;
        }
      }
      break;
    
    // Move Z axis up for 0.5mm increments
    case MOVE_Z:
      Serial.println("STAT(Moving Z axis up - step ");
      Serial.println(zStepCount + 1);

      // Move Z up for 0.5mm increment
      // With 2mm pitch rod and 400 steps/rev (1/2 microstepping), each step = 0.005mm
      // For 0.5mm movement, use 100 steps
      for (int i = 0; i < 100; i++) {
        stepZ(1); // Move Z one microstep
      }

      // Z moved 0.5mm (100 steps * 0.005mm per step)
      z_axis_total_distance += 0.5; // 0.5mm per layer
      zStepCount++;

      // Reset Y parameters for this Z level
      yStepCount = 0;
      y_axis_total_distance = 0.0;
      scanState = MOVE_Y;
      break;
    
    // Complete state
    case DONE:
      if (digitalRead(limitSwitchTop) == LOW) {
        Serial.println("STAT(Top limit reached. Stopping scan.)");
      } else {
        Serial.println("STAT(Scan completed successfully.)");
      }
      homingComplete = false;
      running = false;
      stopFlag = true;
      scanState = IDLE;
      digitalWrite(ENABLE_PIN, HIGH); // disable steppers
      break;
  }
  // Small delay to prevent overwhelming the system
  delay(1);
}
