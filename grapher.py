from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
import queue

class DataGrapher(QObject):
    newData = pyqtSignal(list)  # Signal to main thread for new data
    stopRequested = pyqtSignal() # Signal to stop the grapher
    stopped = pyqtSignal()  # Signal to indicate the grapher has stopped

    def __init__(self, data_queue):
        super().__init__()
        self.data = data_queue
        self.running = False
        self.canvas = None
        self.ax = None
        self.total_graph_data = []
        self.timer = None

        self.stopRequested.connect(self.stop)

    @pyqtSlot()
    def run(self):
        self.running = True

        # Start a timer to poll the queue periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.pollQueue)
        self.timer.start(100)  # Poll every 100 ms

    @pyqtSlot()
    def pollQueue(self):
        if not self.running:
            return
        try:
            data_array = self.data.get_nowait()
            self.newData.emit(data_array)  # Emit to main thread
        except queue.Empty:
            pass

    @pyqtSlot(list)
    def updateModel(self, data):
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
        self.running = False

        # Stop the running timer
        if self.timer:
            self.timer.stop()
            self.timer = None

        self.stopped.emit()  # Emit stopped signal to main thread

    def set_canvas(self, canvas, ax):
        self.canvas = canvas
        self.ax = ax