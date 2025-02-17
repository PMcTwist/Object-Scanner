#include <Arduino.h>  // every sketch needs this
#include <Wire.h>     // instantiate the Wire library
#include <TFLI2C.h>   // TFLuna-I2C Library v.0.2.0
#include <AccelStepper.h>   // Stepper Library

// ========= Setup the LiDAR sensor global variables ========
// This section is for the X-axis
TFLI2C tflI2C;

int16_t tfDist;                // distance in centimeters
int16_t tfAddr = TFL_DEF_ADR;  // use this default I2C address

// ========== Platform global Variables =====================
// This section is for the Y-axis
const float y_StepAngle = 1.8;
const float platformRadius = 100; // in mm

// Platform Calculation Functions
const float stepsPerRev = 360/y_StepAngle;
const float platformCircumference = 2.0 * 3.1415926535 * platformRadius;
const float y_DistancePerStep = platformCircumference / stepsPerRev;

// ========= Threaded Rod Global Variables ===================
// This section is for the Z-axis
const float rodPitch = 2; // in mm
const float z_DistancePerStep = rodPitch / stepsPerRev;




// ======== Setup the Stepper global variables ===============
#define ENABLE_PIN 8   // Enables the CNC sheild 

#define motorYInterfaceType 1
#define motorZInterfaceType 1

// Setup Y Axis Stepper
#define Y_STEP_PIN 3
#define Y_DIR_PIN 6

AccelStepper stepperY(motorYInterfaceType, Y_STEP_PIN, Y_DIR_PIN);

// Setup Z Axis Stepper
#define Z_STEP_PIN 4
#define Z_DIR_PIN 7

AccelStepper stepperZ(motorZInterfaceType, Z_STEP_PIN, Z_DIR_PIN);


// ========= Setup the state of the machine ========================
bool running = false;         // flag for state
bool stopFlag = true;         // flag for system interupt

// Variable to hold travel distances
float x_dist = 0.0;
float y_axis_total_distance = 0.0;
float z_axis_total_distance = 0.0;

// Array of data to send
int dataArray[3];


// Initialization Function
void setup() {
  Serial.begin(115200);           // initialize serial port
  Wire.begin();                   // initialize Wire library

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);  // Enable CNC shield drivers

  // Setup Stepper speeds
  stepperY.setMaxSpeed(500);
  stepperZ.setMaxSpeed(500);

  // Set intial flag for running state
  running = false;
  stopFlag = false;

}

// Runtime Function
void loop() {
  // Check for initial start signal
  checkForUpdates();

  // Basic condition for running state (scanning)
  if (running) {
    // Setup conditional for reading LiDAR data
    if (tflI2C.getData(tfDist, tfAddr))
    {
      // For every step in 360deg of Y motor scan
      // Then move up 1 step on the Z motor 
      for (int z = 0; z < 200; z++){
        // Check for Serial commands
        checkForUpdates();

        if (!stopFlag) {
          // Make Z Step
          stepperZ.move(1);
          stepperZ.run();

          // Update the total Z distance
          z_axis_total_distance += z_DistancePerStep;

          for (int y = 0; y < 200; y++) {
            // Check for Serial Commands
            checkForUpdates();

            if (!stopFlag) {
              // Make Y Step
              stepperY.move(1);
              stepperY.run();

              // update the total Y distance
              y_axis_total_distance += y_DistancePerStep;

              // Meansure X Distance from Sensor and convert to mm
              x_dist = tfDist * 10;
            } if (stopFlag) {
              break; // Kills inner loop on stop code
            }
          }
        } if (stopFlag) {
          break; // Kills the main for loop on stop code
        }

        // Update the dataArray to hold the X, Y, Z values to send to HMI
        dataArray[0] = x_dist;
        dataArray[1] = y_axis_total_distance; 
        dataArray[2] = z_axis_total_distance;

        // Create a string with the array values separated by commas
        String dataToSend = String(dataArray[0]) + "," + String(dataArray[1]) + "," + String(dataArray[2]);


        // Send the string to the Python listener
        Serial.println(dataToSend);
      }    
    } else {
      stepperY.stop();
      stepperZ.stop();
      tflI2C.printStatus();
    }  

    // Set Delay between scans
    delay(500);
  }
  // Avoid breaking the communication
  delay (50);
}

void checkForUpdates() {
  if (Serial.available() > 0) {      // Check if there's serial input
    char inputChar = Serial.read();  // Read the input character from the UI button
    Serial.println(inputChar);
    if (inputChar == '1') {          // Start scanning
      if (!running){
        running = true;
        stopFlag = false;
      Serial.println("Scanning...");
      }
    } else if (inputChar == '0') {   // Stop scanning
      if (running) {
        running = false;
        stopFlag = true;
        Serial.println("Scanning Stopped");
      }
    }
  }
}
