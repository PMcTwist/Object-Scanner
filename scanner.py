# Basic package imports
import sys
import os
import glob
import configparser
import datetime

# Import communication packages
import serial

# PyQt5 UI imports
import PyQt5.uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread

# Custom Packages
from worker import Worker


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
        self.setupUi(self)

        # Instance variables for real time data
        self.thread = None
        self.worker = None

        # Get the current directory
        self.path = os.getcwd()

        # Grab Local Config Info
        self.config_file = configparser.ConfigParser()
        self.config_file.read(self.path + "\\Config\\config.ini")

        # Scan for a list of available ports
        port_list = self.serial_ports()
        self.portCombo.addItems(port_list)

        # Find the usb connected devices
        self.port = serial.Serial(
            port=None, 
            baudrate=0, 
            timeout=0
            )
        
        # Set the empty array to store the scan data
        self.saveData = []
        
        # Call the button handler function to connect the UI to methods
        self.button_handler()
        
    def button_handler(self):
        """
        Function to handle the button clicks and connect them to the functions
        """
        self.pushButtonStart.clicked.connect(self.startScan)
        self.pushButtonStop.clicked.connect(self.stopScan)
        self.pushButtonSave.clicked.connect(self.saveFile)

    def startScan(self):
        """
        Function to start the scanning process
        Input: Button click
        Output: Serial command 1 to arduino
        """
        # Grab the updated port info
        self.updatePort()
        self.updateBaud()
        self.updateTimeout()

        # Update the status label
        self.statusLabel.setText("Scanning...")

        # Send the start signal to the arduino
        self.port.write(bytes('1', 'utf-8'))

        # Start the worker thread and start a worker instance
        self.worker = Worker(
            serial_port=self.port,
            baud=self.baudRate,
            timeout=self.timeOut
            )
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # Conenct to the instance and wait for data
        self.thread.started.connect(self.worker.run)
        self.worker.error_text.connect(self.error_handler)
        self.worker.distance_reading.connect(self.update_distance)
        self.thread.start()

        self.pushButtonStop.setEnabled(True)
        self.pushButtonStart.setEnabled(False)

    def error_handler(self, error):
        """
        Function to handle the error messages
        Input: Error message
        Output: Error message to the status label
        """
        self.statusLabel.setText(error)
        
    def stopScan(self):
        """
        Function to stop the scanning process
        Input: Button click
        Output: Serial command 0 to arduino
        """
        self.port.write(bytes('0', 'utf-8'))
        self.statusLabel.setText("Scanning Stopped")

        self.thread.terminate()

        self.pushButtonStop.setEnabled(False)
        self.pushButtonStart.setEnabled(True)

    def updatePort(self):
        """
        Fucntion to update the port information
        Input: Combobox selection
        Output: Updated port information to class variable
        """
        self.comPort = self.portCombo.currentText()

    def updateBaud(self):
        """
        Function to update the baud rate information
        Input: Combobox selection  
        Output: Updated baud rate information to class variable
        """
        self.baudRate = int(self.baudCombo.currentText())

    def updateTimeout(self):
        """
        Function to update the timeout information
        Input: Combobox selection
        Output: Updated timeout information to class variable
        """
        self.timeOut = int(self.timeoutCombo.currentText())

    def updateDisatace(self, distance):
        """
        Function to update the distance information
        Input: Distance reading from worker thread
        Output: Updated distance information to the UI
        """
        # Display last scanned data to the label
        self.rawDataLabel.setText(distance)

        # Append data to the save array
        self.saveData.append(distance)

    def saveFile(self):
        """
        Function to save the scanned data to a file
        Input: Button click
        Output: Save the data to a file
        """
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Open the file and write the save array
        with open(self.path + f"\\Data\\{timestamp}-scanData.csv", "w") as file:
            for data in self.saveData:
                file.write(data + "\n")

    @staticmethod
    def serial_ports():
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system

            Function by: tfeldmann
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result




if __name__ == "__main__":
    # Create the application instance
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())