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
            # Connect to database
            conn = sqlite3.connect(self.data)
            cursor = conn.cursor()
            
            # Get any new records since last_id
            cursor.execute("""
                SELECT id, x, y, z 
                FROM scan_data 
                WHERE id > ? 
                ORDER BY id ASC
            """, (self.last_id,))
            
            new_data = cursor.fetchall()
            
            for row in new_data:
                self.last_id = row[0]  # Update last processed ID
                data_array = [row[1], row[2], row[3]]  # x, y, z values
                self.newData.emit(data_array)
                
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

        # Data is already (x, y, z)
        self.total_graph_data.append(data)
        self.ax.clear()

        # Check for graph and plot
        if self.total_graph_data:
            xs, ys, zs = zip(*self.total_graph_data)
            self.ax.scatter(xs, ys, zs, color='blue')

        self.canvas.draw()

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