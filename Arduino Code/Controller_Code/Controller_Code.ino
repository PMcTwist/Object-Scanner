// #include <Arduino.h>  // every sketch needs this
// #include <Wire.h>     // instantiate the Wire library
// #include <TFLI2C.h>   // TFLuna-I2C Library v.0.2.0

// TFLI2C tflI2C;

// int16_t tfDist;                // distance in centimeters
// int16_t tfAddr = TFL_DEF_ADR;  // use this default I2C address

// bool running = false;         // flag for state

// void setup() {
//   Serial.begin(115200);                              // initialize serial port
//   Wire.begin();                                      // initialize Wire library

//   // Set intial flag for running state
//   running = false;

// }

// void loop() {

//   if (Serial.available() > 0) {      // Check if there's serial input
//     char inputChar = Serial.read();  // Read the input character from the UI button
//     if (inputChar == '1') {          // Start scanning
//       running = true;
//       Serial.println("Scanning Started");
//     } else if (inputChar == '0') {   // Stop scanning
//       running = false;
//       Serial.println("Scanning Stopped");
//     }
//   }


//   // Basic condition for running state (scanning)
//   if (running == true) {
//     // Setup conditional for reading LiDAR data
//     if (tflI2C.getData(tfDist, tfAddr))
//     {
//       Serial.print("Dist: ");
//       Serial.println(tfDist);     
//     } else tflI2C.printStatus();  

//     // Set Delay between scans
//     delay(5000);
//   }
  
// }