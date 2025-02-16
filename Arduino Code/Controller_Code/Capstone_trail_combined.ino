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
const float stepAngle = 1.8;
const float platformRadius = 100; // in mm

// Platform Calculation Functions
const float stepsPerRev = 360/stepAngle;
const float platformCircumference = 2.0 * 3.1415926535 * platformRadius;
const float y-DistancePerStep = platformCircumference / stepsPerRev;

// ========= Threaded Rod Global Variables ===================
// This section is for the Z-axis



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

// Variable to hold travel distances
const float y-axis_total_distance = 0.0;
const float z-axis_total_distance = 0.0;


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

}

// Runtime Function
void loop() {

  if (Serial.available() > 0) {      // Check if there's serial input
    char inputChar = Serial.read();  // Read the input character from the UI button
    if (inputChar == '1') {          // Start scanning
      running = true;
      Serial.println("Scanning Started");
    } else if (inputChar == '0') {   // Stop scanning
      running = false;
      Serial.println("Scanning Stopped");
    }
  }


  // Basic condition for running state (scanning)
  if (running == true) {
    // Setup conditional for reading LiDAR data
    if (tflI2C.getData(tfDist, tfAddr))
    {
      // For every step in 360deg of Y motor scan
      // Then move up 1 step on the Z motor 
      for (int z = 0; z < 200; z++){
        // Make Z Step
        stepperZ.move(1);
        stepperZ.runToPosition();

        z-axis_total_distance += z-DistancePerStep;

        for (int y = 0; y < 200; y++) {
          // Make Y Step
          stepperY.move(1);
          stepperY.runToPosition();

          // update the total Y distance
          y-axis_total_distance += y-DistancePerStep;

          // Meansure X Distance from Sensor
          Serial.println(tfDist, -2);
        }
      }    
    } else {
      tflI2C.printStatus();
    }  

    // Set Delay between scans
    delay(5000);
  }
  
}