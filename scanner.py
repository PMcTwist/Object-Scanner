# Basic package imports
import sys
import os
import glob
import configparser
import datetime
import queue
import csv

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
        # Set the empty array to store the scan data to save
        self.saveData = []
        # Create a thread-safe queue to store data to graph
        self.data_queue = queue.Queue()

        # Create the worker thread and worker instance
        self.data_thread = QThread()
        self.worker = Worker(self.port)

        # Create the graph thread and grapher instance
        self.graph_thread = QThread()
        self.grapher = DataGrapher(self.data_queue)

        # Send obejcts to the grapher thread
        self.grapher.set_canvas(self.canvas, self.ax) 
        self.grapher.newData.connect(self.grapher.updateModel)

        
        # ============ UI Event Handler Call ============ #
        # Update the status label
        self.statusLabel.setText("Ready!")
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
        # Grab the updated port info from UI
        self.updatePort()
        self.updateBaud()
        self.updateTimeout()

        # Update the status label
        self.statusLabel.setText("Scanning...")

        # Connect to the instance and wait for data
        self.data_thread.started.connect(self.worker.run)
        self.worker.message_received.connect(self.updateStatusLabel)
        self.worker.error_text.connect(self.error_handler)
        self.worker.distance_reading.connect(self.updateDistance)
        
        # Connect the grapher thread to the worker thread
        self.graph_thread.started.connect(self.grapher.run)

        # Move instances to threads
        self.worker.moveToThread(self.data_thread)
        self.grapher.moveToThread(self.graph_thread)

        # Start both threads
        self.data_thread.start()
        self.graph_thread.start()


        self.pushButtonStop.setEnabled(True)
        self.pushButtonStart.setEnabled(False)

    def updateStatusLabel(self, message):
        """
        Function to update the status label with a message
        Input: Message to from worker thread
        Output: Updated status label with message
        """
        self.statusLabel.setText(message)

    def error_handler(self, error):
        """
        Function to handle the error messages
        Input: Error message from worker thread
        Output: Error message to the serial label
        """
        self.serialLabel.setText(error)
        
    def stopScan(self):
        """
        Function to stop the scanning process
        Input: Button click
        Output: Serial command 0 to arduino
        """
        self.statusLabel.setText("Scanning Stopped")

        # Stop the worker thread
        self.worker.stop()               
        self.data_thread.quit()          # Tell the thread to exit its event loop
        self.data_thread.wait()          # Wait for the thread to actually exit

        # Stop the grapher thread
        self.grapher.stop()               
        self.graph_thread.quit()          # Tell the thread to exit its event loop
        self.graph_thread.wait()          # Wait for the thread to actually exit

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

        if distance:
            try:
                # Display last scanned data to the label
                self.rawDataLabel.setText(str(distance))

                # Break data in x, y, z block to be appended
                data_block = [distance[0], distance[1], distance[2]]

                # Append data block to the save array
                self.saveData.append(data_block)
                self.data_queue.put(data_block)
            except Exception as e:
                print(e)
        else:
            pass

    def saveFile(self):
        """
        Function to save the scanned data to a text file
        Input: Button click
        Output: Save the data to a .txt file
        """
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Open the file and write the save array as text
        with open(self.path + f"\\Data\\{timestamp}-scanData.txt", "w") as file:
            for row in self.saveData:
                line = ','.join(str(item) for item in row)
                file.write(line + '\n')

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