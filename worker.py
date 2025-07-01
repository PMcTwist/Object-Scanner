from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import serial
import re
import time

class Worker(QObject):
    """ Worker thread for running loops """
    # Signal to send distance reading
    distance_reading = pyqtSignal(tuple)

    # Signal to send messages
    message_received = pyqtSignal(str)

    # Any returned errors
    error_text = pyqtSignal([str])

    # Signals to stop the worker
    stopRequested = pyqtSignal() 
    stopped = pyqtSignal()

    def __init__(self, port_name, baud, timeout, *args, **kwargs):
        super(Worker, self).__init__()
        self.args = args
        self.kwargs = kwargs

        # Serial port parameters
        self.port_name = port_name
        self.baudrate = baud
        self.timeout = timeout if timeout > 0 else 0.1 # sets a default timeout
        self.open_port = None

        # Flags for connection errors
        self.unplugged = 0

        # Flag to check if the thread is running
        self.running = False

        self.stopRequested.connect(self.stop)

    @pyqtSlot()
    def run(self):
        """
        Function to run the worker thread
        Input: Serial port and data return from TF-Luna Sensor
        Output: Distance reading
        """
        # Set running Flag to true
        self.running = True

        # Open the serial port
        if not self._open_serial_port():
            self.stopped.emit()  # Always emit stopped signal
            return
        
        # try:
        #     self.open_port = serial.Serial(
        #         port=self.port_name,
        #         baudrate=self.baudrate,
        #         timeout=self.timeout
        #     )
        # except serial.SerialException as e:
        #     self.error_text.emit(str(e))
        #     self.unplugged = 1
        #     return
        
        # # Check the port is open
        # if self.open_port.is_open:
        #     print("Port is open!")
        # else:
        #     print("Port is closed.")

        # time.sleep(1)  # Allow time for the port to stabilize

        # # Main loop

        # Send the start signal to the arduino
        if not self._send_start_signal():
            self._cleanup_and_stop()
            return

        # try:
        #     print("Sending start signal to Arduino")
        #     self.open_port.write(bytes('1', 'utf-8'))
        #     self.open_port.flush()
        #     print(f"Start signal sent to {self.open_port.name}")
        # except serial.SerialException as e:
        #     self.error_text.emit(str(e))
        #     self.unplugged = 1


        # Main data reading loop
        self._run_data_loop()

        # while self.running:
        #     try:
        #         serial_returned = self.open_port.readline().decode("utf-8").strip()
                
        #         # Check for STAT() message
        #         stat_match = re.match(r"STAT\((.*)\)", serial_returned)
        #         if stat_match:
        #             self.message_received.emit(stat_match.group(1))
        #         else:
        #             # Check for DATA(x,y,z) format
        #             xyz_tuple = self.is_valid_xyz_data(serial_returned)
        #             if xyz_tuple:
        #                 self.distance_reading.emit(xyz_tuple)
        #     except serial.SerialException as e:
        #         # Handle serial port errors
        #         self.error_text.emit(str(e))
        #         self.unplugged = 1

        # Cleanup
        self._cleanup_and_stop()

        # # After loop exits, send stop signal and close port
        # try:
        #     print("Sending stop signal to Arduino")
        #     self.open_port.write(bytes('0', 'utf-8'))
        #     print("Stop signal sent")
        # except Exception as e:
        #     self.error_text.emit(str(e))
        # try:
        #     self.open_port.close()
        # except Exception as e:
        #     self.error_text.emit(str(e))
        # self.stopped.emit()

    def _open_serial_port(self):
        """
        Open serial port with error handling
        Input: Called from run() method
        Output: True if successful, False if failed
        """
        try:
            self.open_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            if self.open_port.is_open:
                print(f"Port {self.port_name} opened successfully!")
                time.sleep(2)  # Allow port to stabilize
                return True
            else:
                self.error_text.emit("Failed to open port")
                return False
                
        except serial.SerialException as e:
            self.error_text.emit(f"Serial port error: {str(e)}")
            self.unplugged = 1
            return False
        except Exception as e:
            self.error_text.emit(f"Unexpected error opening port: {str(e)}")
            return False

    def _send_start_signal(self):
        """
        Send start signal to Arduino with error handling
        Input: Called from run() method
        Output: True if successful, False if failed
        """
        if not self.running:
            return False
            
        try:
            print("Sending start signal to Arduino")
            self.open_port.write(bytes('1', 'utf-8'))  # Use bytes for compatibility
            self.open_port.flush()  # Ensure immediate transmission
            print(f"Start signal sent to {self.open_port.name}")
            time.sleep(0.1)  # Give Arduino time to process
            return True
            
        except serial.SerialException as e:
            self.error_text.emit(f"Failed to send start signal: {str(e)}")
            self.unplugged = 1
            return False

    def _run_data_loop(self):
        """
        Main data reading loop with non-blocking reads
        Input: Called from run() method
        Output: Reads data from the serial port and emits signals
        """
        while self.running and self.open_port and self.open_port.is_open:
            try:
                # Use a short timeout to prevent blocking
                if self.open_port.in_waiting > 0:
                    serial_returned = self.open_port.readline().decode("utf-8").strip()
                    
                    if serial_returned:  # Only process non-empty strings
                        # Check for STAT() message
                        stat_match = re.match(r"STAT\((.*)\)", serial_returned)
                        if stat_match:
                            self.message_received.emit(stat_match.group(1))
                        else:
                            # Check for DATA(x,y,z) format
                            xyz_tuple = self.is_valid_xyz_data(serial_returned)
                            if xyz_tuple:
                                self.distance_reading.emit(xyz_tuple)
                else:
                    # Small delay
                    time.sleep(0.01)
                            
            # Improved error handling
            except serial.SerialException as e:
                self.error_text.emit(f"Serial communication error: {str(e)}")
                self.unplugged = 1
                break
            except UnicodeDecodeError as e:
                self.error_text.emit(f"Data decode error: {str(e)}")
                continue
            except Exception as e:
                self.error_text.emit(f"Unexpected error in data loop: {str(e)}")
                break

    def _cleanup_and_stop(self):
        """
        Clean shutdown of serial connection
        Input: Stop signal from main window
        Output: Close the serial port if it is open
        """
        # Send the stop signal to the Arduino
        if self.open_port and self.open_port.is_open:
            try:
                print("Sending stop signal to Arduino")
                self.open_port.write(bytes('0', 'utf-8'))  # Use bytes for compatibility
                self.open_port.flush()
                print("Stop signal sent")
            except Exception as e:
                self.error_text.emit(f"Error sending stop signal: {str(e)}")
            
            # Close the serial port
            try:
                self.open_port.close()
                print("Serial port closed")
            except Exception as e:
                self.error_text.emit(f"Error closing port: {str(e)}")

        self.stopped.emit()

    @pyqtSlot()
    def stop(self):
        """
        Function to stop the worker thread
        Input: Stop signal from main window
        Output: Set running flag to false
        """
        print("Stopping worker thread")
        self.running = False

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
            print(f"Error parsing data: {data} : {e}")
            return None