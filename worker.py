from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import serial
import re

class Worker(QObject):
    """ Worker thread for running loops """
    # Signal to send distance reading
    distance_reading = pyqtSignal(tuple)

    # Signal to send messages
    message_received = pyqtSignal(str)

    # Any returned errors
    error_text = pyqtSignal([str])

    stopRequested = pyqtSignal() # Signal to stop the worker

    def __init__(self, serial_port, *args, **kwargs):
        super(Worker, self).__init__()
        self.args = args
        self.kwargs = kwargs

        # Flags for connection errors
        self.unplugged = 0

        # Port sent by main class to worker class for use
        self.open_port = serial_port

        # Flag to check if the thread is running
        self.running = True

        self.stopRequested.connect(self.stop)

    @pyqtSlot()
    def run(self):
        """
        Function to run the worker thread
        Input: Serial port and data return from TF-Luna Sensor
        Output: Distance reading
        """

        # Open the serial port
        try:
            self.open_port.open()
        except serial.SerialException as e:
            self.error_text.emit(str(e))
            self.unplugged = 1

        # Main loop

        # Send the start signal to the arduino
        try:
            self.open_port.write(bytes('1', 'utf-8'))
        except serial.SerialException as e:
            self.error_text.emit(str(e))
            self.unplugged = 1

        while self.running:
            try:
                serial_returned = self.open_port.readline().decode("utf-8").strip()
                
                # Check for STAT() message
                stat_match = re.match(r"STAT\((.*)\)", serial_returned)
                if stat_match:
                    self.message_received.emit(stat_match.group(1))
                else:
                    # Check for DATA(x,y,z) format
                    xyz_tuple = self.is_valid_xyz_data(serial_returned)
                    if xyz_tuple:
                        self.distance_reading.emit(xyz_tuple)
            except serial.SerialException as e:
                # Handle serial port errors
                self.error_text.emit(str(e))
                self.unplugged = 1

    @pyqtSlot()
    def stop(self):
        """
        Function to stop the worker thread
        Input: Stop signal from main window
        Output: Set running flag to false
        """
        self.open_port.write(bytes('0', 'utf-8'))
        
        self.running = False
        
        self.open_port.close()

    def is_valid_xyz_data(self, data):
        """
        Checks if the input string is in the format DATA(x,y,z).
        Input: data (str): The input string to validate.
        Output: tuple or None: Returns (x, y, z) as floats if valid, or None if invalid.
        """
        try:
            # Match pattern like DATA(1.0,2.0,3.0)
            pattern = r"^DATA\(\s*(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)\s*\)$"
            match = re.match(pattern, data.strip())
            if match:
                # Extract numbers from inside the parentheses
                nums = match.groups()
                x = float(nums[0])
                y = float(nums[2])
                z = float(nums[4])
                return x, y, z
            else:
                return None
        except Exception as e:
            print(f"Error parsing data: {e}")
            return None