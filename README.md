# 3D Scanner

This project is a capstone for UWindsors mechatronics program. We wanted to kick it up a notch and build a custom UI for PC integration as well as a stand alone touch ui driven by raspberry pi. 
The hardware of the project is driven by Arduino Uno and Raspberry Pi.

## Basic Design

The basic concept is an x, y, z measurement taken from a rotating platform with a threaded rod with a distance sensor on it. Pretty simple in concept. 

![First CAD](/Assets/assets/model.jpg)

## Implemenatation

We started out with a few Nema17 motors, TF-Luna LiDAR sensor, and an arduino. 

![Basics](/Assets/assets/week1-layout.jpg)

From there a basic UI was made with PyQt5 and QtDesigner.

![Basic UI](/Assets/assets/UI.jpg)

Including a CNC shield board and A4988 drivers to drive the motors allowed for microstepping for a better resolution of scan.

![Mechanical Mock up](/Assets/assets/week3-mockup.jpg)

To take it over the top, the addition of a raspberry pi and touch screen for serial control of the scanner and real time model rendering.

![UI Mock up](/Assets/assets/week4_HMI_2.jpg)

Next, updating the CAD to refelct the real components and the measurments we need for a frame.

![CAD Update](/Assets/assets/week4-CAD.jpg)


## Setup

Users can extract the provided exe (For Windows) in releases or use the Pi-HMI directly on the device. Linux users can use the python files directly or setup the same system service we called. 

The scanner has two modes of operation. <br/>
   1 - Pi-HMI <br/>
   2 - USB Interface 

## Contacts
🤓 - Kevin -  <br/>
🤬 - Pat - patmaynard452@hotmail.com

---