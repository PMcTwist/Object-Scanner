
// Variables
const float stepAngle = 1.8;
const float platformRadius = 100; // in mm

// calculation functions
const float stepsPerRev = 360/stepAngle;
const float platformCircumference = 2.0 * 3.1415926535 * platformRadius;
const float distancePerStep = platformCircumference / stepsPerRev;

// Variable to hold travel distance
const float y-axis_total_distance = 0.0;

// update the total distance
y-axis_total_distance += distancePerStep;

