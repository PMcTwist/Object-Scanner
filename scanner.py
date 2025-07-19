# Basic package imports
import sys
import os
import glob
import configparser
import datetime
import queue
import csv
import sqlite3

# Import communication packages
import serial

import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 backend for matplotlib

# Import plotting packages
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# PyQt5 UI imports
import PyQt5.uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QFileDialog
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

        # ===== Data Variables ===== #
        self.saveData = []

        # ===== SQLite3 Setup =====
        self.db_path = os.path.join(self.path, "Data", "scan_data.db")
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()

        # ========== Serial Communication Stuff ========== #.
        # Scan for a list of available ports
        port_list = self.serial_ports()
        self.portCombo.addItems(port_list)
        
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
        
        # ============ UI Event Handler Call ============ #
        # Update the status labels
        self.statusLabel.setText("Ready!")
        self.serialLabel.setText(" ")
        # Call the button handler function to connect the UI to methods
        self.button_handler()
        
    def button_handler(self):
        """
        Function to handle the button clicks and connect them to the functions
        """
        self.pushButtonStart.clicked.connect(self.startScan)
        self.pushButtonStop.clicked.connect(self.stopScan)
        self.pushButtonSave.clicked.connect(self.saveFile)

    def _create_table(self):
        """ 
        Function to create the SQLite3 table for scan data
        Input: None
        Output: Creates a table if it does not exist
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                x REAL,
                y REAL,
                z REAL,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def startScan(self):
        """
        Function to start the scanning process
        Input: Button click
        Output: Serial command 1 to arduino
        """
        # Cleanup any previous scan threads
        self._cleanup_previous_scan()  

        # Grab the updated port info from UI
        self.updatePort()
        self.updateBaud()
        self.updateTimeout()

        # Update the status label
        self.statusLabel.setText("Scanning...")

        # =========== Threading Stuff =========== #
        # Set the empty array to store the scan data to save
        self.saveData = []
        # Create a thread-safe queue to store data to graph
        self.data_queue = queue.Queue()

        # Create and setup worker thread
        self._setup_worker_thread()
        
        # Create and setup grapher thread
        self._setup_grapher_thread()

        # Start both threads
        self.data_thread.start()
        self.graph_thread.start()


        # ====== Set Button States ====== #
        self.pushButtonStop.setEnabled(True)
        self.pushButtonStart.setEnabled(False)

    def _cleanup_previous_scan(self):
        """
        Properly cleanup previous scan threads
        Input: None
        Output: Stops existing threads and clears references
        """
        # Stop existing workers
        if hasattr(self, 'worker') and self.worker:
            self.worker.stopRequested.emit()
        if hasattr(self, 'grapher') and self.grapher:
            self.grapher.stopRequested.emit()
        
        # Wait for threads to finish
        if hasattr(self, 'data_thread') and self.data_thread:
            if self.data_thread.isRunning():
                self.data_thread.quit()
                self.data_thread.wait(3000)  # Wait max 3 seconds
        
        if hasattr(self, 'graph_thread') and self.graph_thread:
            if self.graph_thread.isRunning():
                self.graph_thread.quit()
                self.graph_thread.wait(3000)
        
        # Clear references
        self.worker = None
        self.grapher = None
        self.data_thread = None
        self.graph_thread = None

        # Clear scan data from database file
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM scan_data")
        self.conn.commit()

    def _setup_worker_thread(self):
        """
        Setup worker thread with proper connections
        Input: None
        Output: Worker thread ready to run
        """
        self.data_thread = QThread()
        self.worker = Worker(
            self.portCombo.currentText(),
            int(self.baudCombo.currentText()),
            int(self.timeoutCombo.currentText())
        )
        self.worker.moveToThread(self.data_thread)
        
        # Connect signals
        self.data_thread.started.connect(self.worker.run)
        self.worker.message_received.connect(self.updateStatusLabel)
        self.worker.error_text.connect(self.error_handler)
        self.worker.distance_reading.connect(self.updateDistance)
        self.worker.stopped.connect(self.on_worker_stopped)

    def _setup_grapher_thread(self):
        """
        Setup grapher thread with proper connections
        Input: None
        Output: Grapher thread ready to run
        """
        self.graph_thread = QThread()
        self.grapher = DataGrapher(self.db_path)
        self.grapher.moveToThread(self.graph_thread)
        
        # Set canvas and connect signals
        self.grapher.set_canvas(self.canvas, self.ax)
        self.grapher.newData.connect(self.grapher.updateModel)
        self.graph_thread.started.connect(self.grapher.run)
        self.grapher.stopped.connect(self.on_grapher_stopped)

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

        # Stop the worker and grapher threads
        if hasattr(self, 'worker'):
            self.worker.stopRequested.emit()
        if hasattr(self, 'grapher'):
            self.grapher.stopRequested.emit()

        self.pushButtonStop.setEnabled(False)
        self.pushButtonStart.setEnabled(True)

    def on_worker_stopped(self):
        """
        Function to handle the worker thread stopped signal
        Input: Worker thread stopped signal
        Output: Quit and wait for the worker thread to finish
        """
        self.data_thread.quit()
        self.data_thread.wait()

    def on_grapher_stopped(self):
        """
        Function to handle the grapher thread stopped signal
        Input: Grapher thread stopped signal
        Output: Quit and wait for the grapher thread to finish
        """
        self.graph_thread.quit()
        self.graph_thread.wait()

    def updatePort(self):
        """
        Function to update the port information
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
                # self.saveData.append(data_block)

                # Insert into SQLite3
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO scan_data (x, y, z) VALUES (?, ?, ?)",
                    (data_block[0], data_block[1], data_block[2])
                )
                self.conn.commit()

                # Put the data block into the queue for grapher thread
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

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Scan Data", f"{timestamp}-scanData.txt", "CSV Files (*.csv);;All Files (*)"
        )

        # Connect to the database and grab the data
        cursor = self.conn.cursor()
        cursor.execute("SELECT x, y, z FROM scan_data")
        rows = cursor.fetchall()

        # Check for filename to avoid crashing
        if filename:
            # Open the file and write the save array as text
            with open(filename, "w") as file:
                for row in rows:
                    line = ','.join(str(item) for item in row)
                    file.write(line + '\n')
        else:
            # If no filename is selected update the status label
            self.statusLabel.setText("No file selected for saving.")

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