from PyQt5.QtCore import QThread, pyqtSignal
import time

class MeasurementControlThread(QThread):
    status_update = pyqtSignal(str)  # optional: Textnachrichten an GUI
    finished = pyqtSignal()

    def __init__(self, data_measurement, track_function, parent=None):
        super().__init__(parent)
        self.data = data_measurement
        self.track_function = track_function
        self.running = True

    def run(self):
        self.status_update.emit("Measurement started.")
        while self.running:
            try:
                self.status_update.emit("tracking...")
                self.track_function(self.data)
                self.status_update.emit("tracking complete...")          


                #time.sleep(0.1)  # Optional: kleine Pause für Responsiveness
            except Exception as e:
                self.status_update.emit(f"Error during tracking: {e}")
                break
        self.status_update.emit("Measurement stopped.")
        self.finished.emit()

    def stop(self):
        self.running = False
