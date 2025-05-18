from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox,
    QGroupBox, QTextEdit, QDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

from container import String_Chuck_Container
from helpers import load_measurement_from_yaml
from dialogs import MeasurementEditDialog

from threads import MeasurementControlThread
from Measurement_engine import track,set_all_cells_to_voltage
from old_drivers import initialize_boards

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

button_scaling_factor = 0.5
import os



class FullscreenButtonWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fullscreen Button GUI")

        self.measurement = load_measurement_from_yaml(os.path.join("DATA","settings.yaml"))
        self.loaded_chucks = self.measurement.string_chucks
        self.measurement_thread = None

        # Initialize the Octoboards and append the data to the measurement object. 
        initialize_boards(self.measurement)
        # Set all channels to 0.5V
        set_all_cells_to_voltage(Data_Measurement=self.measurement, voltage=0.5)

        #Now perform a fast J-V Scan 

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Top Bar mit Info Panel ---
        top_bar_layout = QHBoxLayout()
        self.create_measurement_info_panel()
        top_bar_layout.addWidget(self.info_box)
        main_layout.addLayout(top_bar_layout)

        # --- String Chuck Container Buttons ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.button_containers = []

        for chuck_data in self.loaded_chucks:
            container = String_Chuck_Container(data=chuck_data,measurement_data = self.measurement)
            container.update_display()
            self.button_containers.append(container)
            button_layout.addWidget(container, alignment=Qt.AlignBottom)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def create_measurement_info_panel(self):
        self.info_box = QGroupBox("  Measurement Info")
        self.info_box.setFixedSize(int(800*button_scaling_factor), int(200*button_scaling_factor))

        self.info_layout = QVBoxLayout()
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.update_info_display()

        # Klick auf Info Panel öffnet Editor
        self.info_text.mousePressEvent = lambda event: self.open_measurement_editor()

        # Steuerbuttons
        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")

        self.start_button.clicked.connect(self.start_measurement)
        self.pause_button.clicked.connect(self.pause_measurement)
        self.stop_button.clicked.connect(self.stop_measurement)

        button_row = QHBoxLayout()
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.pause_button)
        button_row.addWidget(self.stop_button)

        self.info_layout.addWidget(self.info_text)
        self.info_layout.addLayout(button_row)
        self.info_box.setLayout(self.info_layout)

    def update_info_display(self):
        m = self.measurement
        text = f"ID: {m.id}\nUser: {m.user}\nAlgorithm: {m.mpp_algorithm}\nFolder: {m.local_folder}"
        self.info_text.setText(text)

    def open_measurement_editor(self):
        dialog = MeasurementEditDialog(self.measurement)
        if dialog.exec_() == QDialog.Accepted:
            self.update_info_display()

    def start_measurement(self):
        if self.measurement_thread is None or not self.measurement_thread.isRunning():
            
            self.measurement_thread = MeasurementControlThread(self.measurement, track)
            self.measurement_thread.status_update.connect(self.handle_thread_status)
            self.measurement_thread.finished.connect(self.on_measurement_finished)
            self.measurement_thread.start()
            self.info_text.append("[INFO] Measurement started.")
        else:
            QMessageBox.information(self, "Already Running", "Measurement is already running.")

    def pause_measurement(self):
        QMessageBox.information(self, "Pause", "Pause-Funktion ist aktuell nicht implementiert.")

    def stop_measurement(self):
        if self.measurement_thread and self.measurement_thread.isRunning():
            self.measurement_thread.stop()
            self.info_text.append("[INFO] Stop signal sent.")

    def handle_thread_status(self, message):
        self.info_text.append(f"[STATUS] {message}")

    def on_measurement_finished(self):
        self.measurement_thread = None
        self.info_text.append("[INFO] Measurement finished.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

# Main App Start
app = QApplication([])

app.setStyleSheet("QWidget { font-size: 7pt; }")  # oder 10pt

window = FullscreenButtonWindow()

window.showFullScreen()

app.exec_()
