from PyQt5.QtCore import QThread, pyqtSignal
import queue

class DataGrapher(QThread):
    def __init__(self, data_queue, progressBar):
        super().__init__()
        # Progress signal
        self.progressBar = progressBar

        # Data queue shared with main thread
        self.data = data_queue

        # State Flag
        self.running = True

        # Placeholder variables to be passed in
        self.canvas = None
        self.ax = None
        self.last_z = []

    def run(self):
        """
        Main graph loop
        Input: Serial Data
        Output: Updated model widget
        """
        while self.running:
            try:
                # Wait for data to be available in the queue
                data_array = self.data_queue.get(timeout=1)
                self.check_and_update_graph(data_array)
            except queue.Empty:
                continue

    def set_canvas(self, canvas, ax):
        """
        Set the canvas and axes for the grapher worker.
        Input: Main thread passes the canvas and axes objects
        Output: Set the canvas and axes objects for the thread instance
        """
        self.canvas = canvas
        self.ax = ax

    def check_and_update_graph(self, data_array):
        """
        Check if any `z` values have changed, and if so, update the graph.
        Input: Data array from the scanner
        Output: Data passed to graph updater
        """
        print("trying to update graph")
        # Extract the z-values from the new data array
        new_z_values = [data[2] for data in data_array]

        # Only update the graph if any z-value has changed
        if new_z_values != self.last_z:
            # Calculate the progress
            progress = len([z for z in new_z_values if z > 0]) / len(new_z_values) * 100
            self.updateProgress(progress)

            # Update the model
            self.last_z = new_z_values
            self.updateModel(data_array)

    def updateModel(self, data):
        """
        Function to update the model widget
        Input: Model data from array used to plot model
        Output: Updated model widget on UI
        """
        if not self.running or not self.canvas:
            return

        for i in data:
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

    def updateProgress(self, progress):
        """
        Function to update the progress bar
        Input: Progress Z value from check_and_update_graph
        Output: Updated progress bar on UI
        """
        if not self.running or not self.progressBar:
            return

        self.progressBar.setValue(progress)

    def stop(self):
        """
        Stop the grapher thread.
        Input: Stop signal from main thread
        Output: Set the running flag to False
        """
        self.running = False