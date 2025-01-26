# Basic package imports
import sys
import os
import configparser

# Import communication packages
import serial

# PyQt5 UI imports
import PyQt5.uic
from PyQt5.QtWidgets import QApplication, QMainWindow


# Setup relative path and grab UI file
path = os.getcwd()
ui_path = os.path.join(path, "Assets", "scanner.ui")
print(ui_path)
FORM_CLASS, _ = PyQt5.uic.loadUiType(ui_path)

# Main window class
class MainWindow(QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        QMainWindow.__init__(self)

        # Instance variables for real time data
        self.thread = None
        self.worker = None

        # Get the current directory
        self.path = os.getcwd()

        # Grab Local Config Info
        self.config_file = configparser.ConfigParser()
        self.config_file.read(self.path + "\\Config\\config.ini")

        self.ports_info = self.config_file['Communication']
        self.comPort = self.ports_info['port']
        self.baudRate = self.ports_info['baudrate']
        self.timeOut = int(self.ports_info['timeout'])

        # Find the usb connected devices
        self.port = serial.Serial(
            port=self.comPort, 
            baudrate=self.baudRate, 
            timeout=self.timeOut
            )
        
    def button_handler(self):
        self.pb_start.clicked.connect(self.startScan)
        self.pb_quit.clicked.connect(self.stopScan)

    def startScan(self):
        # Grab the updated port info
        self.updatePort()
        self.updateBaud()
        self.updateTimeout()

        # Send the start signal to the arduino
        self.port.write(b'1')
        # Update the status label
        self.statusLabel.setText("Scanning...")

    def stopScan(self):
        self.port.write(b'0')
        self.statusLabel.setText("Scanning Stopped")

    def updatePort(self):
        self.comPort = self.portCombo.currentText()

    def updateBaud(self):
        self.baudRate = int(self.baudCombo.currentText())

    def updateTimeout(self):
        self.timeOut = int(self.timeoutCombo.currentText())

if __name__ == "__main__":
    # Create the application instance
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())