# Basic package imports
import sys
import os
import configparser

# Import communication packages
import serial

# PyQt5 UI imports
import PyQt5.uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget


# Setup relative path and grab UI file
path = os.getcwd()
FORM_CLASS, _ = PyQt5.uic.loadUiType(path + "\\UI\\scanner.ui")

# Main window class
class MainWindow(QMainWindow, FORM_CLASS):
    def __init__(self):
        super().__init__()

        # Instance variables for real time data
        self.thread = None
        self.worker = None

        # Get the current directory
        self.path = os.getcwd()

        # Grab Local Config Info
        self.config_file = configparser.ConfigParser()
        self.config_file.read(self.path + "\\Config\\config.ini")

        # Find the usb connected devices
        self.port = serial.Serial(port='COM3', baudrate=115200, timeout=1)
        print(self.port)

if __name__ == "__main__":
    # Create the application instance
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())