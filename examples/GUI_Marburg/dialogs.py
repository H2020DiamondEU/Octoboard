from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QComboBox,
    QListWidget, QListWidgetItem, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from Data_Classes import Data_Measurement, Data_String_Chuck
import os
from helpers import export_yaml, create_folder_if_not_exists
from container import configure_data_by_type

class MeasurementEditDialog(QDialog):
    def __init__(self, data: Data_Measurement):
        super().__init__()

        self.data = data
        self.setWindowTitle("Edit Measurement")
        self.setGeometry(400, 400, 400, 600)

        layout = QVBoxLayout()

        # ID
        self.id_input = QLineEdit(self.data.id)
        layout.addWidget(QLabel("Measurement ID:"))
        layout.addWidget(self.id_input)

        # User
        self.user_input = QLineEdit(self.data.user)
        layout.addWidget(QLabel("User:"))
        layout.addWidget(self.user_input)

        # Local_Folder
        self.local_folder_input = QLineEdit(self.data.local_folder)
        layout.addWidget(QLabel("Local Folder:"))
        layout.addWidget(self.local_folder_input)

        # Network_Folder
        self.network_folder_input = QLineEdit(self.data.network_folder)
        layout.addWidget(QLabel("Network_Folder:"))
        layout.addWidget(self.network_folder_input)

        # MPP Algorithm
        self.alg_combo = QComboBox()
        self.alg_combo.addItems([
            "PERTURB_AND_OBSERVE"
        ])
        self.alg_combo.setCurrentText(self.data.mpp_algorithm)
        layout.addWidget(QLabel("MPP Algorithm:"))
        layout.addWidget(self.alg_combo)

        # String Chuck Auswahl
        self.string_chuck_list = QListWidget()
        self.string_chuck_list.setSelectionMode(QListWidget.MultiSelection)
        for chuck in self.data.string_chucks:
            item = QListWidgetItem(f"Chuck {chuck.position} - {chuck.id}")
            item.setCheckState(Qt.Checked if chuck.active else Qt.Unchecked)
            item.setData(Qt.UserRole, chuck)
            self.string_chuck_list.addItem(item)

        layout.addWidget(QLabel("Active String Chucks:"))
        layout.addWidget(self.string_chuck_list)

        # === Zusätzliche Parameter ===
        self.power_increase_input = QDoubleSpinBox()
        self.power_increase_input.setDecimals(2)
        self.power_increase_input.setRange(0.0, 10.0)
        self.power_increase_input.setSingleStep(0.1)
        self.power_increase_input.setValue(self.data.CHANNEL_POWER_INCREASE_FACTOR)
        layout.addWidget(QLabel("Power Increase Factor:"))
        layout.addWidget(self.power_increase_input)

        self.power_decrease_input = QDoubleSpinBox()
        self.power_decrease_input.setDecimals(2)
        self.power_decrease_input.setRange(0.0, 10.0)
        self.power_decrease_input.setSingleStep(0.1)
        self.power_decrease_input.setValue(self.data.CHANNEL_POWER_DECREASE_FACTOR)
        layout.addWidget(QLabel("Power Decrease Factor:"))
        layout.addWidget(self.power_decrease_input)

        self.jvscan_cycle_input = QSpinBox()
        self.jvscan_cycle_input.setRange(1, 100000)
        self.jvscan_cycle_input.setValue(self.data.interval_next_JV)
        layout.addWidget(QLabel("Minimum time (s) until next JV measurement:"))
        layout.addWidget(self.jvscan_cycle_input)

        self.iterations_input = QSpinBox()
        self.iterations_input.setRange(1, 1000)
        self.iterations_input.setValue(self.data.BOARD_DEFAULT_ITERATIONS)
        layout.addWidget(QLabel("Default Iterations per Channel:"))
        layout.addWidget(self.iterations_input)

        self.interval_input = QDoubleSpinBox()
        self.interval_input.setDecimals(4)
        self.interval_input.setRange(0.0001, 10.0)
        self.interval_input.setSingleStep(0.001)
        self.interval_input.setValue(self.data.BOARD_DEFAULT_INTERVAL)
        layout.addWidget(QLabel("Default Tracking Interval (s):"))
        layout.addWidget(self.interval_input)

        self.stepsize_jv_input = QDoubleSpinBox()
        self.stepsize_jv_input.setDecimals(4)
        self.stepsize_jv_input.setRange(0.001, 5.0)
        self.stepsize_jv_input.setSingleStep(0.048)
        self.stepsize_jv_input.setValue(self.data.stepsize_JV)
        self.stepsize_jv_input.valueChanged.connect(self.update_sweep_rate)
        layout.addWidget(QLabel("JV Sweep Stepsize (V):"))
        layout.addWidget(self.stepsize_jv_input)

        # Fixe Settling Time
        self.settletime_jv_input = QDoubleSpinBox()
        self.settletime_jv_input.setDecimals(3)
        self.settletime_jv_input.setRange(0.001, 5.0)
        self.settletime_jv_input.setSingleStep(0.01)
        self.settletime_jv_input.setValue(0.1)
        self.settletime_jv_input.setDisabled(True)  # Eingabe deaktivieren
        layout.addWidget(QLabel("JV Sweep Settling Time (s):"))
        layout.addWidget(self.settletime_jv_input)

        # Sweep Rate-Anzeige
        self.sweep_rate_label = QLabel("")
        layout.addWidget(QLabel("Sweep Rate (V/s):"))
        layout.addWidget(self.sweep_rate_label)
        self.update_sweep_rate()

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
    
    def update_sweep_rate(self):
        stepsize = self.stepsize_jv_input.value()
        sweep_rate = stepsize / 0.9  # 0.1 settling time plus time for ADCs
        self.sweep_rate_label.setText(f"{sweep_rate:.3f} V/s")


    def save_data(self):
        # Grunddaten übernehmen
        self.data.id = self.id_input.text()
        self.data.user = self.user_input.text()
        self.data.local_folder = self.local_folder_input.text()
        self.data.network_folder = self.network_folder_input.text()
        self.data.mpp_algorithm = self.alg_combo.currentText()

        # Tracking-/JV-Parameter übernehmen
        self.data.BOARD_DEFAULT_ITERATIONS = self.iterations_input.value()
        self.data.BOARD_DEFAULT_INTERVAL = self.interval_input.value()
        self.data.stepsize_JV = self.stepsize_jv_input.value()
        self.data.settletime_JV = self.settletime_jv_input.value()
        self.data.CHANNEL_POWER_INCREASE_FACTOR = self.power_increase_input.value()
        self.data.CHANNEL_POWER_DECREASE_FACTOR = self.power_decrease_input.value()
        self.data.interval_next_JV = self.jvscan_cycle_input.value()

        # String Chucks aktualisieren
        for i in range(self.string_chuck_list.count()):
            item = self.string_chuck_list.item(i)
            chuck = item.data(Qt.UserRole)
            chuck.active = item.checkState() == Qt.Checked
            configure_data_by_type(chuck)

        # Lokalen Ordner erstellen & speichern
        create_folder_if_not_exists(self.data.local_folder)
        export_yaml(self.data, os.path.join(self.data.local_folder, "settings.yaml"))

        # Netzwerkordner erstellen & speichern
        create_folder_if_not_exists(self.data.network_folder)
        export_yaml(self.data, os.path.join(self.data.network_folder, "settings.yaml"))

        self.accept()

