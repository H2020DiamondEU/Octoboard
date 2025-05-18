from Data_Classes import Data_String_Chuck, Data_Substrate
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox,
    QDialog, QLabel, QComboBox, QLineEdit, QCheckBox, QSpinBox,
    QGroupBox, QFormLayout, QHBoxLayout, QDoubleSpinBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

from old_drivers import Blink, select_channel
import matplotlib.pyplot as plt
import numpy as np
from helpers import get_mpp_from_j_v_data
import os

ICON_FOLDER = os.path.join(os.path.dirname(__file__), "icons")

button_scaling_factor = 0.6

class String_Chuck_Container(QWidget):
    def __init__(self, data: Data_String_Chuck = None, measurement_data = None):
        super().__init__()
        self.data = data
        self.measurement_data = measurement_data

        self.setFixedSize(int(300*button_scaling_factor), int(1087*button_scaling_factor))
      
        # Set icon based on type
        self.main_button = QPushButton(self)
        self.main_button.setIcon(QIcon(os.path.join(ICON_FOLDER, self.data.icon)))
        self.main_button.setIconSize(QSize(int(129*button_scaling_factor), int(1087*button_scaling_factor)))
        self.main_button.setFixedSize(int(129*button_scaling_factor), int(1087*button_scaling_factor))
        self.main_button.setStyleSheet("border: none;")
        self.main_button.move(int(120*button_scaling_factor), 0)  # Centered position
        self.main_button.clicked.connect(self.show_info)


        self.update_subbuttons()

    def update_subbuttons(self): 
        # Funktion, die die Bilder der Subbuttons updated
        # Remove existing sub-buttons from the GUI
        if hasattr(self, 'sub_buttons'):
            for sub_button, _ in self.sub_buttons:
                sub_button.deleteLater()
        
        self.sub_buttons = []

        # Create new sub-buttons based on the updated data
        for i, substrate in enumerate(self.data.substrates):
            if substrate is None or substrate.slot_index is None:
                continue  # Skip empty slots

            sub = QPushButton(self)
            sub.setFixedSize(int(40 * button_scaling_factor), int(40 * button_scaling_factor))

            sub.setIcon(QIcon(os.path.join(ICON_FOLDER, substrate.icon)))
            # Set icon based on substrate type
            sub.clicked.connect(lambda _, b=i: self.open_substrate_dialog(b))
            sub.show()

            # Statt direkt rel_y speichern wir das Substrat und seinen Slot-Index
            self.sub_buttons.append((sub, substrate.slot_index))

        # Position the newly created sub-buttons
        self.position_sub_buttons()



    def open_substrate_dialog(self, index: int):
        substrate = self.data.substrates[index]
        dialog = SubstrateEditDialog(substrate, self.measurement_data )
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.update_subbuttons()



    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_sub_buttons()

    def position_sub_buttons(self):
        for sub_button, slot_index in self.sub_buttons:
            if slot_index is None or slot_index >= len(self.data.relative_substrate_positions):
                continue  # Sicherstellen, dass der Index gültig ist

            x = self.main_button.x() + int(self.main_button.width() / 2) - int(20 * button_scaling_factor)
            rel_y = self.data.relative_substrate_positions[slot_index]
            y = self.main_button.y() + int(self.main_button.height() * rel_y) - int(20 * button_scaling_factor)
            sub_button.move(x, y)



    def show_dialog(self, text):
        msg = QMessageBox(self)
        msg.setWindowTitle("Info")
        msg.setText(f"{text}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        

    def show_info(self):
        dialog = StringChuckEditDialog(self.data)
        dialog.exec_()
        self.update_display()

    def update_display(self):
        self.main_button.setIcon(QIcon(os.path.join(ICON_FOLDER, self.data.icon)))
        self.update_subbuttons()


class StringChuckEditDialog(QDialog):
    def __init__(self, data: Data_String_Chuck):
        super().__init__()

        self.data = data
        self.setWindowTitle("Edit String Chuck")
        self.setGeometry(400, 400, 400, 250)

        layout = QVBoxLayout()

        # Type selection
        self.type_label = QLabel("Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MR", "EPFL"])
        self.type_combo.setCurrentText(self.data.type)
        self.type_combo.currentTextChanged.connect(self.type_changed)
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_combo)

        # Cell Slots (Read-Only, will be set automatically)
        self.cell_slots_label = QLabel("Number of Cell Slots (Automatic):")
        self.cell_slots_input = QSpinBox()
        self.cell_slots_input.setRange(0, 10)
        self.cell_slots_input.setValue(self.data.cell_slots)
        self.cell_slots_input.setEnabled(False)  # Disabled, set automatically
        layout.addWidget(self.cell_slots_label)
        layout.addWidget(self.cell_slots_input)

        # ID Number
        self.id_label = QLabel("ID Number:")
        self.id_input = QLineEdit(self.data.id)
        layout.addWidget(self.id_label)
        layout.addWidget(self.id_input)

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def type_changed(self):
        # When the type is changed, update icon and cell_slots automatically     
        self.data.type = self.type_combo.currentText()
        configure_data_by_type(self.data)

        #self.icon_combo.setCurrentText(self.data.type)
        self.cell_slots_input.setValue(self.data.cell_slots)

    def save_data(self):
        # Save only the allowed fields
        self.data.type = self.type_combo.currentText()
        self.data.cell_slots = self.cell_slots_input.value()
        self.data.id = self.id_input.text()
        
        self.accept()  # Close the dialog

class SubstrateEditDialog(QDialog):
    def __init__(self, substrate, measurement_data=None):
        super().__init__()

        self.measurement_data = measurement_data
        self.substrate = substrate

        self.setWindowTitle(f"Edit Substrate: {substrate.id}")
        self.setGeometry(400, 400, 500, 600)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # --- Substrate ID ---
        self.id_input = QLineEdit(self.substrate.id)
        self.layout.addWidget(QLabel("Substrate ID:"))
        self.layout.addWidget(self.id_input)

        # --- Batch Number ---
        self.batch_input = QLineEdit(self.substrate.batch_number)
        self.layout.addWidget(QLabel("Batch Number:"))
        self.layout.addWidget(self.batch_input)

        # --- Type ---
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MR", "EPFL", "Sensor_Device", "Resistor", "Not Active"])
        self.type_combo.setCurrentText(self.substrate.type)
        self.type_combo.currentTextChanged.connect(self.substrate_type_changed)  
        self.layout.addWidget(QLabel("Type:"))
        self.layout.addWidget(self.type_combo)

        # Active
        self.active_combo = QLineEdit("Active" if self.substrate.active else "Not Active")
        self.active_combo.setEnabled(False)
        self.layout.addWidget(QLabel("Active?:"))
        self.layout.addWidget(self.active_combo)


        # --- Number of Cells ---
        self.cell_count_input = QSpinBox()
        self.cell_count_input.setRange(1, 64)
        self.cell_count_input.setValue(self.substrate.number_of_cells)
        self.cell_count_input.valueChanged.connect(self.rebuild_cell_inputs)
        self.layout.addWidget(QLabel("Number of Cells:"))
        self.layout.addWidget(self.cell_count_input)

        # --- Cells Group ---
        self.cell_group = QGroupBox("Cells")
        self.cell_inputs_layout = QFormLayout()
        self.cell_group.setLayout(self.cell_inputs_layout)
        self.layout.addWidget(self.cell_group)

        self.cell_widgets = []
        self.rebuild_cell_inputs()

        # --- Button Row: Save + Blink + JV ---
        button_row = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_data)
        button_row.addWidget(self.save_button)

        self.blink_button = QPushButton("Blink")
        self.blink_button.clicked.connect(self.call_blink)
        button_row.addWidget(self.blink_button)

        self.jv_button = QPushButton("JV")
        self.jv_button.clicked.connect(self.call_jv)
        button_row.addWidget(self.jv_button)

        self.layout.addLayout(button_row)

    def call_blink(self):
        Blink(self.substrate, self.measurement_data)

    

    def call_jv(self):
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()  # second y-axis for resistance

        for cell in self.substrate.cells:
            select_channel(cell.TCA_Channel)
            corresponding_manager = self.measurement_data.oboard_managers[cell.TCA_Channel]
            corresponding_oboard = corresponding_manager.oboards[cell.Octoboard_number]
            corresponding_channel = corresponding_oboard.channel[cell.Channel]

            v_set, voltage, current = corresponding_channel.JV_Sweep(self.measurement_data, cell)
            resistance = np.array(voltage) / np.where(np.array(current) == 0, np.nan, current)

            label = f"Cell {cell.Channel}"
            ax1.plot(voltage, current, label=f"JV - {label}")
            ax2.plot(voltage, resistance, 'k:', label=f"R=V/I - {label}")

            # Get MPP point
            _, v_mpp, i_mpp = get_mpp_from_j_v_data(v_set, voltage, current)
            r_mpp = v_mpp / i_mpp if i_mpp != 0 else np.nan

            # Mark MPP point
            ax1.plot(v_mpp, i_mpp, 'ro')
            ax1.text(v_mpp, i_mpp, f"MPP:\n{v_mpp:.2f}V\n{i_mpp:.2f}A", fontsize=8, color='red')

            # Label resistance at MPP
            ax2.text(v_mpp, r_mpp, f"{r_mpp:.1f}Ω", fontsize=8, color='black')

        # Axis setup
        ax1.set_xlabel("Voltage (V)")
        ax1.set_ylabel("Current (A)", color="blue")
        ax2.set_ylabel("Resistance (Ω)", color="black")
        ax1.tick_params(axis='y', labelcolor='blue')
        ax2.tick_params(axis='y', labelcolor='black')

        plt.title("JV Curve with MPP and Resistance")
        ax1.legend(loc="upper left", fontsize="small")
        ax2.legend(loc="upper right", fontsize="small")
        ax1.grid(True)
        fig.tight_layout()
        plt.show()


    def rebuild_cell_inputs(self):
    # Bestehende Widgets entfernen
        for i in reversed(range(self.cell_inputs_layout.count())):
            self.cell_inputs_layout.itemAt(i).widget().setParent(None)

        self.cell_widgets = []
        cell_count = self.cell_count_input.value()

        # Auffüllen, falls nicht genug Zellen vorhanden sind
        while len(self.substrate.cells) < cell_count:
            new_id = len(self.substrate.cells)
            self.substrate.cells.append(Data_Cell(
                id=new_id,
                TCA_Channel=0,
                Octoboard_number=0,
                Channel=0,
                voltage_limits_JV=[-0.1, 1.2]
            ))

        for i in range(cell_count):
            cell = self.substrate.cells[i]

            cell_layout = QHBoxLayout()
            container = QWidget()
            container.setLayout(cell_layout)

            # Cell ID
            id_input = QLineEdit()
            id_input.setText(str(cell.id))
            id_input.setReadOnly(True)  # <- Benutzer kann nichts ändern
            cell_layout.addWidget(QLabel("ID:"))
            cell_layout.addWidget(id_input)

            # TCA Channel
            tca_input = QSpinBox()
            tca_input.setValue(cell.TCA_Channel)
            tca_input.setEnabled(False)
            cell_layout.addWidget(QLabel("TCA:"))
            cell_layout.addWidget(tca_input)

            # Octoboard Number
            ob_input = QSpinBox()
            ob_input.setValue(cell.Octoboard_number)
            ob_input.setEnabled(False)
            cell_layout.addWidget(QLabel("OB:"))
            cell_layout.addWidget(ob_input)

            # Channel
            ch_input = QSpinBox()
            ch_input.setValue(cell.Channel)
            ch_input.setEnabled(False)
            cell_layout.addWidget(QLabel("CH:"))
            cell_layout.addWidget(ch_input)


            # Max Current
            max_current = QDoubleSpinBox()
            max_current.setRange(0.0, 1.0)
            max_current.setDecimals(6)
            max_current.setValue(cell.max_allowed_current)
            cell_layout.addWidget(QLabel("I_max (A):"))
            cell_layout.addWidget(max_current)

            # Voltage min
            v_min = QDoubleSpinBox()
            v_min.setRange(-5.0, 5.0)
            v_min.setDecimals(3)
            v_min.setValue(cell.voltage_limits_JV[0])
            cell_layout.addWidget(QLabel("V_min JV (V):"))
            cell_layout.addWidget(v_min)

            # Voltage max
            v_max = QDoubleSpinBox()
            v_max.setRange(-5.0, 5.0)
            v_max.setDecimals(3)
            v_max.setValue(cell.voltage_limits_JV[1])
            cell_layout.addWidget(QLabel("V_max JV (V):"))
            cell_layout.addWidget(v_max)

            # Alle Widgets speichern
            self.cell_widgets.append((id_input, tca_input, ob_input, ch_input, max_current, v_min, v_max))
            self.cell_inputs_layout.addRow(container)



    def save_data(self):
        self.substrate.id = self.id_input.text()
        self.substrate.batch_number = self.batch_input.text()
        self.substrate.number_of_cells = self.cell_count_input.value()
        #self.substrate_type_changed(self.substrate.type) 

        # Zellenwerte übernehmen
        for i, widgets in enumerate(self.cell_widgets):
            id_input, tca_input, ob_input, ch_input, max_current, v_min, v_max = widgets
            cell = self.substrate.cells[i]
            cell.id = id_input.text()
            cell.TCA_Channel = tca_input.value()
            cell.Octoboard_number = ob_input.value()
            cell.Channel = ch_input.value()
            cell.max_allowed_current = max_current.value()
            cell.voltage_limits_JV = [v_min.value(), v_max.value()]

        # Nur die richtige Anzahl an Zellen speichern
        self.substrate.cells = self.substrate.cells[:self.substrate.number_of_cells]

        self.accept()


    def substrate_type_changed(self, new_type):
        if new_type == "Not Active":
            self.substrate.icon = "Empty_Substrate_Slot.png"
            self.substrate.active = False
            # Jetzt auch das Icon übernehmen
        # GUI Felder anpassen, aber noch NICHT in self.substrate schreiben
        elif new_type == "MR":
            self.cell_count_input.setValue(4)
            self.substrate.active = True
            for cell_widgets in self.cell_widgets:
                _, _, _, _, max_current, v_min, v_max = cell_widgets
                v_min.setValue(-0.3)
                v_max.setValue(1.15)
                max_current.setValue(0.05)

            self.substrate.icon  = "UMR_Cell_Design.png"

        elif new_type == "EPFL":
            self.cell_count_input.setValue(1)
            self.substrate.active = True
            for cell_widgets in self.cell_widgets:
                _, _, _, _, max_current, v_min, v_max = cell_widgets
                v_min.setValue(-0.1)
                v_max.setValue(1.2)
                max_current.setValue(0.02)

            self.substrate.icon  = "EPFL_Cell_Design.png"

        elif new_type == "Sensor_Device":
            self.cell_count_input.setValue(4)
            self.substrate.active = True
            # Jetzt individuelle Werte pro Kanal:
            sensor_defaults = [
                {"v_min": -0.2, "v_max": 1.25, "max_current": 0.005},
                {"v_min": -0.2, "v_max": 0.2, "max_current": 0.00025}, # R_TEMP 1 0.25mA max, 1kOhm, 
                {"v_min": -0.2, "v_max": 1.25, "max_current": 0.005},
                {"v_min": -0.2, "v_max": 0.2, "max_current": 0.00025},
            ]

            for cell_widgets, settings in zip(self.cell_widgets, sensor_defaults):
                _, _, _, _, max_current, v_min, v_max = cell_widgets
                v_min.setValue(settings["v_min"])
                v_max.setValue(settings["v_max"])
                max_current.setValue(settings["max_current"])

            self.substrate.icon  = "Sensor_Device.png"
    
        elif new_type == "Resistor":
            self.cell_count_input.setValue(1)
            self.substrate.active = True
            for cell_widgets in self.cell_widgets:
                _, _, _, _, max_current, v_min, v_max = cell_widgets
                v_min.setValue(0.0)
                v_max.setValue(5.0)
                max_current.setValue(0.0001)

            self.substrate.icon  = "Resistor.png"

def configure_data_by_type(data: Data_String_Chuck):
    if data.active == False: 
        data.icon = "Empty_Slot.png"
    elif data.type == "MR":
        data.icon = "String_Chuck_MR.png"
        data.cell_slots = 10
        data.relative_substrate_positions = [1 - 42 / 500 - 30 / 500 * k for k in reversed(range(10))]
    elif data.type == "EPFL":
        data.icon = "String_Chuck_EPFL.png"
        data.cell_slots = 16
        data.relative_substrate_positions = [1 - 42 / 500 - 21 / 500 * k for k in reversed(range(16))]


       