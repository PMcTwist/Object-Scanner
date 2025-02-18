from PyQt5.QtCore import QThread, pyqtSignal
import re

class DataGrapher(QThread):
    data_generated = pyqtSignal([str])  # Signal to send raw data

    def run(self):
        while True:
            # Get the raw data from the worker thread
            raw_data = self.get_data()
            
            # Check if the data is valid
            if self.is_valid_xyz_data(raw_data):
                # Send the data to the main thread to save later
                self.data_generated.emit(raw_data)

                # Update the graph with the new data
                self.updateModel()
            else:
                print("Invalid data received")

    def is_valid_xyz_data(self, data):
        """
        Checks if the input string is a valid CSV representing (x, y, z) coordinates.
        Input: data (str): The input string to validate.
        Output: tuple or None: Returns (x, y, z) as floats if valid, or None if invalid.
        """
        try:
            # Check if the data matches the pattern "float, float, float"
            pattern = r"^(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)$"
            match = re.match(pattern, data.strip())

            if match:
                # Extract and convert to floats
                x, y, z = map(float, data.split(","))
                # print(f"Valid data parsed: x={x}, y={y}, z={z}")
                return x, y, z
            else:
                print("Invalid data format: Does not match expected pattern")
                return None
        except Exception as e:
            print(f"Error parsing data: {e}")
            return None
        
    def updateModel(self):
        """
        Function to update the model widget
        Input: Model data from array used to plot model
        Output: Updated model widget on UI
        """
        for i in self.saveData:
            # Unpack the data
            x = i[0]
            y = i[1]
            z = i[2]

            # Remove the old plot
            self.ax.clear()

            # Plot the updated surface
            self.ax.scatter(x, y, z, color='blue')

        # Redraw the canvas with updates
        self.canvas.draw()