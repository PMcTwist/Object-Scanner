from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
import queue

class DataGrapher(QObject):
    # Progress signal
    updateProgressSignal = pyqtSignal(int) 


    def __init__(self, data_queue, progressBar):
        super().__init__()
        

        # Data queue shared with main thread
        self.data = data_queue

        # State Flag
        self.running = True

        # Placeholder variables to be passed in
        self.canvas = None
        self.ax = None
        self.last_z = []
        self.total_graph_data = []

    def run(self):
        """
        Main graph loop
        Input: Timer runs when thread is started
        Output: Call to poll the queue for data
        """
        self.timer = QTimer()
        self.timer.timeout.connect(self.pollQueue)
        self.timer.start(1000)

    def pollQueue(self):
        """
        Poll the queue for new data
        Input: Serial Data from queue
        Output: Updated model widget
        """
        try:
            # Wait for data to be available in the queue
            data_array = self.data.get(timeout=1)
            self.check_and_update_graph(data_array)
        except queue.Empty:
            pass

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
        # Extract the z-values from the new data array
        new_z_values = data_array[-1]

        try:
            # Only update the graph if any z-value has changed
            if new_z_values != self.last_z:
                # Calculate the progress
                progress = new_z_values * 2
                self.updateProgress(int(progress))

                # Update the model
                self.last_z = new_z_values
                self.updateModel(data_array)
        except Exception as e:
                print(e)

    def updateModel(self, data):
        """
        Function to update the model widget
        Input: Model data from array used to plot model
        Output: Updated model widget on UI
        """
        if not self.running or not self.canvas:
            return
        
        print(f"Updating model: {data}")
        self.total_graph_data.append(data)

        for i in self.tota_graph_data:
            # Unpack the data
            x = i[0]
            y = i[1]
            z = i[2]

            print(f"Plotting point: x={x}, y={y}, z={z}")

            # Remove the old plot
            self.ax.clear()

            # Plot the updated surface
            self.ax.scatter(x, y, z, color='blue')

        # Redraw the canvas with updates
        self.canvas.draw()

    @pyqtSlot()
    def updateProgress(self, progress):
        """
        Function to update the progress bar
        Input: Progress Z value from check_and_update_graph
        Output: Updated progress bar on UI
        """
        if not self.running:
            return

        print(f"Updating progress: {progress}")

        self.updateProgressSignal.emit(progress)

    def stop(self):
        """
        Stop the grapher thread.
        Input: Stop signal from main thread
        Output: Set the running flag to False
        """
        self.running = False