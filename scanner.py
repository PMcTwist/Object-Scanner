# Basic package imports
import sys
import os
import glob
import configparser
import datetime
import re

# Import communication packages
import serial

# Import plotting packages
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# PyQt5 UI imports
import PyQt5.uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import QThread

# Custom Packages
from worker import Worker
from grapher import DataGrapher


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

        # Get the current directory
        self.path = os.getcwd()

        # Grab Local Config Info
        self.config_file = configparser.ConfigParser()
        self.config_file.read(self.path + "\\Config\\config.ini")

        # ========== Serial Communication Stuff ========== #.
        # Scan for a list of available ports
        port_list = self.serial_ports()
        self.portCombo.addItems(port_list)

        # Find the usb connected devices
        self.port = serial.Serial(
            port=self.portCombo.currentText(), 
            baudrate=int(self.baudCombo.currentText()), 
            timeout=int(self.timeoutCombo.currentText())
            )
        
        # ==========  Graph Stuff ========== #
        # Find the placeholder widget for the model
        placeholder_widget = self.findChild(QWidget, "scanWidget")

        # Create a layout for the placeholder if it doesn't have one
        layout = placeholder_widget.layout()
        if not layout:
            layout = QVBoxLayout(placeholder_widget)
            placeholder_widget.setLayout(layout)

        # Setup the figure and axis for model
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(projection='3d')

        # Initial plot data for 0 point
        self.surface = self.ax.scatter(0, 0, 0, color='blue', marker='o', s=10)
        self.ax.set_aspect('equal')
        # self.ax.axis('off')

        # Create the canvas to render on
        self.canvas = FigureCanvas(self.fig)

        # Add the plot canvas to the placeholder widget's layout
        layout.addWidget(self.canvas)
        
        # =========== Threading Stuff =========== #
        # Set the empty array to store the scan data
        self.saveData = []

        # Create the worker thread and worker instance
        self.data_thread = QThread()
        self.worker = Worker(self.port)

        # Create the graph thread and grapher instance
        self.graph_thread = QThread()
        self.grapher = DataGrapher()
        
        # ============ UI Event Handler Call ============ #
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

        # Move instances to threads
        self.worker.moveToThread(self.data_thread)
        self.grapher.moveToThread(self.graph_thread)

        # Connect to the instance and wait for data
        self.data_thread.started.connect(self.worker.run)
        self.worker.error_text.connect(self.error_handler)
        self.worker.distance_reading.connect(self.updateDistance)
        
        # Connect the grapher thread to the worker thread
        self.grapher.started.connect(self.grapher.run)
        self.grapher.data_generated.connect(self.updateDistance) # Send the data to the main thread

        # Start both threads
        self.data_thread.start()
        self.graph_thread.start()


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
        self.statusLabel.setText("Scanning Stopped")

        self.worker.stop()               
        self.thread.quit()          # Tell the thread to exit its event loop
        self.thread.wait()          # Wait for the thread to actually exit

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

    def updateDistance(self, distance):
        """
        Function to update the distance information
        Input: Distance reading from worker thread
        Output: Updated distance information to the UI
        """
        data = self.is_valid_xyz_data(distance)

        if data:
            # Display last scanned data to the label
            self.rawDataLabel.setText(str(data))

            # Break data in x, y, z block to be appended
            data_block = [data[0], data[1], data[2]]

            # Append data block to the save array
            self.saveData.append(data_block)
        else:
            pass

    # def is_valid_xyz_data(self, data):
    #     """
    #     Checks if the input string is a valid CSV representing (x, y, z) coordinates.
    #     Input: data (str): The input string to validate.
    #     Output: tuple or None: Returns (x, y, z) as floats if valid, or None if invalid.
    #     """
    #     # print(f"Raw data received: '{data}'")

    #     try:
    #         # Check if the data matches the pattern "float, float, float"
    #         pattern = r"^(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)$"
    #         match = re.match(pattern, data.strip())

    #         if match:
    #             # Extract and convert to floats
    #             x, y, z = map(float, data.split(","))
    #             # print(f"Valid data parsed: x={x}, y={y}, z={z}")
    #             return x, y, z
    #         else:
    #             print("Invalid data format: Does not match expected pattern")
    #             return None
    #     except Exception as e:
    #         print(f"Error parsing data: {e}")
    #         return None

    # def updateModel(self):
    #     """
    #     Function to update the model widget
    #     Input: Model data from array used to plot model
    #     Output: Updated model widget on UI
    #     """
    #     for i in self.saveData:
    #         # Unpack the data
    #         x = i[0]
    #         y = i[1]
    #         z = i[2]

    #         # Remove the old plot
    #         self.ax.clear()

    #         # Plot the updated surface
    #         self.ax.scatter(x, y, z, color='blue')

    #     # Redraw the canvas with updates
    #     self.canvas.draw()

    def saveFile(self):
        """
        Function to save the scanned data to a file
        Input: Button click
        Output: Save the data to a file
        """
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

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