
# Object Scanner

A low-cost, real-time 3D scanning platform built using **Python**, **C++**, **Arduino**, **Raspberry Pi**, and **LiDAR** technology.

Originally developed as a capstone project at the **University of Windsor**, Object Scanner was designed to demonstrate that accurate 3D scanning can be achieved using affordable, readily available hardware while providing a modular platform for future development and experimentation.

---

## Project Overview

Commercial 3D scanners are often prohibitively expensive for students, hobbyists, and small organizations. Object Scanner was created to provide an affordable alternative capable of producing real-time point cloud visualizations using open-source software and off-the-shelf hardware.

The system combines embedded firmware, desktop software, and custom hardware into a complete scanning platform capable of:

- Capturing real-time LiDAR/IR measurements
- Controlling dual-axis motion using stepper motors
- Processing scan data on a Raspberry Pi
- Visualizing point cloud data in real time
- Exporting captured scan information for future processing

---

## Features

- Real-time 3D point cloud visualization
- Python desktop application using PyQt5
- Arduino-based motion controller
- Raspberry Pi deployment
- SQLite scan data storage
- Live serial communication between hardware and software
- Configurable scan parameters
- Exportable scan data
- Modular architecture for future sensor upgrades

---

# Technologies

## Software

- Python
- PyQt5
- SQLite
- Matplotlib
- PySerial

## Embedded

- Arduino
- C++
- Stepper Motor Control
- Serial Communication

## Hardware

- Raspberry Pi
- TF-Luna LiDAR / IR Sensor
- NEMA Stepper Motors
- CNC Shield
- A4988 Drivers

---

# System Architecture

```
               +----------------------+
               |    Python GUI        |
               |      (PyQt5)         |
               +----------+-----------+
                          |
                    Serial Connection
                          |
               +----------v-----------+
               |      Arduino         |
               | Motion Controller    |
               +----------+-----------+
                          |
          +---------------+----------------+
          |                                |
   Stepper Motors                    LiDAR / IR Seonsor
          |                                |
          +---------------+----------------+
                          |
                    Scan Coordinates
                          |
               +----------v-----------+
               |    SQLite Database   |
               +----------+-----------+
                          |
               Real-Time 3D Visualization
```

---

# Screenshots

## User Interface

![Basic UI](/Assets/assets/UI.jpg)
![UI Mock up](/Assets/assets/week4_HMI_2.jpg)

---

## Hardware

![First CAD](/Assets/assets/model.jpg)
![Basics](/Assets/assets/week1-layout.jpg)
![Mechanical Mock up](/Assets/assets/week3-mockup.jpg)
![CAD Update](/Assets/assets/week4-CAD.jpg)
![Final Cad](/Assets/assets/FullModel.jpg)

---

## Run-Time

![UI Update](/Assets/assets/realTime.gif)

---

# Repository Structure

```
Object-Scanner/

Arduino/
    Embedded firmware

Assets/
    Images and UI resources

Database/
    SQLite scan database

Models/
    3D printable components

Python/
    Desktop application

Releases/
    Executable releases

Scripts/
    Raspberry Pi startup scripts
```

---

# Installation

## Requirements

- Python 3.11+
- PyQt5
- Matplotlib
- PySerial
- SQLite3

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Running

Launch the application:

```bash
python scanner.py
```

Connect the Arduino via USB and configure the correct COM port before starting a scan.

---

# Future Improvements

Potential future enhancements include:

- Multi-threaded scan processing improvements
- Higher resolution scanning
- Additional sensor support
- Mesh generation
- STL export
- Network-based control
- Improved scan filtering algorithms

---

# Lessons Learned

This project provided valuable experience in:

- Embedded systems
- Python application development
- Hardware/software integration
- Real-time data visualization
- Multithreaded programming
- SQLite databases
- Raspberry Pi deployment
- Project planning
- Team collaboration

---

# Authors

## Patrick Maynard

Software Development  
Software Design • Embedded Systems • Automation

Email: patmaynard452@gmail.com
LinkedIn: https://www.linkedin.com/in/pat-maynard-b97a05b5/

---

## Kevin McClintock

Mechanical Design • Embedded Systems • Automation

Email:
LinkedIn:

---

# License

This project is released under the MIT License.
