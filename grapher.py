from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
import sqlite3

class DataGrapher(QObject):
    newData = pyqtSignal(list)  # Signal to main thread for new data
    stopRequested = pyqtSignal() # Signal to stop the grapher
    stopped = pyqtSignal()  # Signal to indicate the grapher has stopped
    
    # Any returned errors
    error_text = pyqtSignal([str])

    def __init__(self, db_path):
        super().__init__()
        # Setup database path
        self.data = db_path
        # Set the last index to 0
        self.last_id = 0

        # Set flags and initial values
        self.running = False
        self.canvas = None
        self.ax = None
        self.total_graph_data = []
        self.timer = None

        self.stopRequested.connect(self.stop)

    @pyqtSlot()
    def run(self):
        """
        Function to run the grapher thread
        Input: Database path
        Output: Emits newData signal with the latest data
        """
        self.running = True

        # Start a timer to poll the queue periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.pollQueue)
        self.timer.start(100)  # Poll every 100 ms

    @pyqtSlot()
    def pollQueue(self):
        """
        Function to poll the database for new data
        Input: None
        Output: Emits newData signal with the latest data
        """
        if not self.running:
            return
        try:
            conn = sqlite3.connect(self.data)
            cursor = conn.cursor()
            
            # Just check if new data exists
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM scan_data WHERE id > ?
                )
            """, (self.last_id,))
            
            has_new_data = cursor.fetchone()[0]
            
            if has_new_data:
                # Update last_id and signal for update
                cursor.execute("SELECT MAX(id) FROM scan_data")
                self.last_id = cursor.fetchone()[0]

                # Send out an empty signal to update the graph
                self.newData.emit([])
                
            conn.close()
        except sqlite3.Error as e:
            self.error_text.emit(f"Database Error: {str(e)}")

    @pyqtSlot(list)
    def updateModel(self, data):
        """
        Function to update the model with new data
        Input: Data in the form of a list [x, y, z]
        Output: Updates the graph with new data
        """
        if not self.running or not self.canvas or not self.ax:
            return

        try:
            conn = sqlite3.connect(self.data)
            cursor = conn.cursor()
            
            # Get all data points
            cursor.execute("SELECT x, y, z FROM scan_data")
            all_data = cursor.fetchall()
            conn.close()

            if all_data:
                # Clear the current plot
                self.ax.clear()
                
                # Unzip the data directly from database results
                xs, ys, zs = zip(*all_data)
                self.ax.scatter(xs, ys, zs, color='blue')
                
                # Update the plot
                self.canvas.draw()
                
        except sqlite3.Error as e:
            self.error_text.emit(f"Plot Update Error: {str(e)}")

    @pyqtSlot()
    def stop(self):
        """
        Function to stop the grapher thread
        Input: Stop signal from main window
        Output: Set running flag to false and stop the timer
        """
        self.running = False

        # Stop the running timer
        if self.timer:
            self.timer.stop()
            self.timer = None

        self.stopped.emit()  # Emit stopped signal to main thread

    def set_canvas(self, canvas, ax):
        """
        Function to set the canvas and axes for plotting
        Input: canvas (matplotlib canvas), ax (matplotlib axes)
        Output: Sets the canvas and axes for plotting
        """
        self.canvas = canvas
        self.ax = ax