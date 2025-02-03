from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import serial

class Worker(QObject):
    """ Worker thread for running loops """

    distance_reading = pyqtSignal([str])
    # Any returned errors
    error_text = pyqtSignal([str])

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
                # Get the distance reading
                distance_num = self.open_port.readline().decode("utf-8").strip()

                # Send the distance reading to the main thread
                self.distance_reading.emit(distance_num)

            except serial.SerialException as e:
                self.error_text.emit(str(e))
                self.unplugged = 1

    def stop(self):
        """
        Function to stop the worker thread
        Input: Stop signal from main window
        Output: Set running flag to flase
        """
        self.running = False
        self.open_port.write(bytes('0', 'utf-8'))
        self.open_port.close()