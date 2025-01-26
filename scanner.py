# Basic package imports
import sys
import os
import glob
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
        self.setupUi(self)

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

        # Scan for a list of available ports
        port_list = self.serial_ports()
        self.portCombo.addItems(port_list)

        # Find the usb connected devices
        self.port = serial.Serial(
            port=self.comPort, 
            baudrate=self.baudRate, 
            timeout=self.timeOut
            )
        
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
        self.port.write(b'1')
        

    def stopScan(self):
        """
        Function to stop the scanning process
        Input: Button click
        Output: Serial command 0 to arduino
        """
        self.port.write(b'0')
        self.statusLabel.setText("Scanning Stopped")

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

    def saveFile(self):
        pass

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