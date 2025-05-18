import argparse
import board
import busio
import os
import adafruit_mcp4728
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_mcp230xx.mcp23017 import MCP23017
import numpy as np
import matplotlib.pyplot as plt
import time
import csv
from datetime import datetime
from adafruit_blinka.microcontroller.generic_linux.i2c import I2C as _I2C
from adafruit_blinka.microcontroller.generic_linux.spi import SPI as _SPI
from os import path
import threading
from busio import I2C, SPI
import smbus2
import time
from helpers import copy_to_network_drive_gio, create_folder_if_not_exists, get_mpp_from_j_v_data
from datetime import datetime

class ExtendedI2C(I2C):
    """Extended I2C is a busio extension that allows creating a compatible
    of /dev/i2c-# and you can find which I2C devices you have by typing
    ``ls /dev/i2c*``"""

    # pylint: disable=super-init-not-called
    def __init__(self, bus_id, frequency=400000):
        self.init(bus_id, frequency)

    # pylint: enable=super-init-not-called

    # pylint: disable=arguments-differ
    def init(self, bus_id, frequency):
        self.deinit()

        # Check if the file /dev/i2c-{bus_id} exists and error if not
        if not path.exists(f"/dev/i2c-{bus_id}"):
            raise ValueError(f"No device found for /dev/i2c-{bus_id}")
        # Attempt to open using _I2C
        self._i2c = _I2C(bus_id, mode=_I2C.MASTER, baudrate=frequency)

        self._lock = threading.RLock()
        




class OBoardManager:
    """Manages multiple OBoard instances for operations across several I2C boards.

    Attributes:
        oboards (list): A list of OBoard instances.
    """
    def __init__(self, i2c_num=1, possible_offsets=range(0, 4)):
        """Initialize the OBoardManager by scanning I2C devices and setting up boards accordingly."""
        self.oboards = []
        self.i2c_num = i2c_num
        self.i2c = ExtendedI2C(i2c_num)  # Setup I2C using the imported board module
        self.setup_boards(possible_offsets)

    def setup_boards(self, possible_offsets):
        """Scan I2C addresses and initialize boards only if all required devices are detected."""
        while not self.i2c.try_lock():
            pass

        found_devices = set(self.i2c.scan())
        self.i2c.unlock()
        print(f"Found I2C devices at addresses: {found_devices}")

        base_addresses = [32, 72, 96, 97]  # Base addresses for Mux, ADC, DAC_0, DAC_1
        for offset in possible_offsets:
            expected_device_addresses = set([
                base + offset if base in [32, 72] else base + 2 * offset for base in base_addresses
            ])
            if expected_device_addresses.issubset(found_devices):
                try:
                    ob = OBoard(i2c_num=self.i2c_num, i2c_address_offset=offset)
                    self.oboards.append(ob)
                    print(f"Successfully initialized OBoard with I2C offset {offset}")
                except Exception as e:
                    print(f"Failed to initialize board with offset {offset}: {e}")
                    raise(e)
            else:
                print(f"Not all devices found for board with offset {offset}. Expected {expected_device_addresses}, found {found_devices}")

    def cycle_all_channels(self, iterations_per_channel=10, interval=0.001):
        """Cycle through all channels on all boards, performing MPPT tracking."""
        for oboard in self.oboards:
            for channel in oboard.channel:
                channel.mpp_track(iterations=iterations_per_channel, interval=interval)

    def print_all_boards_status(self):
        """Print the status of all boards for debugging purposes."""
        for oboard in self.oboards:
            print(f"Board ID: {oboard.ID}")
            for channel in oboard.channel:
                print(f"Channel ID: {channel.id}, Last Voltage: {channel.last_v}")


class OBoard:
    """Represents a single I2C connected board capable of multiple channel operations.

    Attributes:
        ID (str): Identifier for the board based on configuration.
        i2c_base_address (list): Base addresses for devices connected via I2C.
        ic2_base_devices (list): List of devices on the I2C bus.
        Dac_0 (device): First DAC device on the board.
        Dac_1 (device): Second DAC device on the board.
        Mux (device): Multiplexer on the board.
        Adc (device): ADC device on the board.
        softdac (Softdac): Software-based DAC for fine control.
        channel (list): List of channels controlled by this board.
    """
    def __init__(self, i2c_num=1, i2c_address_offset=2, debug=False):
        """Initialize an OBoard with specified I2C pins and address offset."""
        i2c = ExtendedI2C(i2c_num)
        self.i2c_num = i2c_num
        self.debug = debug
        self.ID = f"Bus_{i2c_num}_offset{i2c_address_offset}_"
        self.i2c_base_address = [32 + i2c_address_offset, 72 + i2c_address_offset, 96 + i2c_address_offset * 2, 97 + i2c_address_offset * 2]
        self.i2c_base_devices = ["mux", "ADC", "DAC_0", "DAC_1"]
        self.Dac_0 = adafruit_mcp4728.MCP4728(i2c, address=96 + 0 + i2c_address_offset * 2)
        self.Dac_1 = adafruit_mcp4728.MCP4728(i2c, address=96 + 1 + i2c_address_offset * 2)
        self.Mux = MCP23017(i2c, address=32 + i2c_address_offset)
        self.Adc = ADS.ADS1115(i2c, gain=1, data_rate=8, address=72 + i2c_address_offset)
        self.softdac = Softdac(self.Mux)
        self.channel = []
        for ch in range(8):
            channel_list = ['channel_a', 'channel_b', 'channel_c', 'channel_d']
            if ch < 4:
                Dac = self.Dac_0
            else:
                Dac = self.Dac_1
            self.channel.append(
                Channel(self,
                        Dac=Dac.__dict__[channel_list[ch % 4]],
                        ind=ch))
                    
        #self.channel = [Channel(self, Dac=self.Dac_0 if ch < 4 else self.Dac_1, ind=ch) for ch in range(8)]

    def print(self, message):
        """Prints a message if debugging is enabled."""
        if self.debug:
            print(message)

    def aMux_enable(self):
        """Enable the analog multiplexer by setting the control pin low."""
        pin = self.Mux.get_pin(7)
        pin.switch_to_output(value=0)

    def aMux_disable(self):
        """Disable the analog multiplexer by setting the control pin high."""
        pin = self.Mux.get_pin(7)
        pin.switch_to_output(value=1)

    def aMux_select_channel(self, channel: int):
        """Select a specific channel on the multiplexer."""
        mux_channel_map = [6, 5, 4, 7, 3, 0, 2, 1]
        if channel < 0 or channel >= len(mux_channel_map):
            raise ValueError("Invalid channel number")
        address = mux_channel_map.index(channel)
        #address = mux_channel_map[channel]
        self.print(f"Selecting logical channel {channel}, which maps to multiplexer channel {address}")
        for x in range(3):
            val = bool(address >> x & 1)
            pin = self.Mux.get_pin(4 + x)
            self.print(f"Setting pin {4 + x} to {'HIGH' if val else 'LOW'}")
            pin.switch_to_output(value=val)

class Softdac:
    """A software-driven DAC utilizing a multiplexer for setting gain voltages.

    Attributes:
        Mux (device): The multiplexer device used to set different gain levels.
        vref (float): Reference voltage for setting the gains.
        MUX_PINS (list): List of pins used in the multiplexer to set gain levels.
        gain_voltages (numpy.array): Array of voltage levels corresponding to different gains.
        reg (numpy.array): Register settings for configuring the MUX pins based on desired gain.
        _gain (int): Current gain level.
    """
    def __init__(self, Mux, vref=3.3):
        """Initialize the Softdac with a multiplexer and a reference voltage."""
        self.Mux = Mux
        self.vref = vref
        self.MUX_PINS = [8, 9, 10, 11]
        self.gain_voltages = np.array([
            0.035, 0.310, 0.656,
            0.930, 1.378, 1.672,
            2.00, 2.29
        ])
        self.reg = np.array(
            [[0, 0, 0, 0],
             [1, 0, 0, 0],
             [0, 1, 0, 0],
             [1, 1, 0, 0],
             [0, 0, 1, 0],
             [1, 0, 1, 0],
             [0, 1, 1, 0],
             [1, 1, 1, 0],
             [0, 0, 0, 1]]
        )
        self.gain = 2
        print(f"initialized softdac with gain of {self.gain}")
        print(f"softdac voltage will be {self.voltage}")

    @property
    def gain(self):
        """Get the current gain setting."""
        return self._gain

    @gain.setter
    def gain(self, gain: int):
        """Set the gain of the soft DAC by configuring the multiplexer pins."""
        if gain < 0 or gain >= len(self.gain_voltages):
            raise ValueError("Invalid gain value.")
        val_array = self.reg[gain, :]
        for ind, val in enumerate(val_array):
            time.sleep(0.1)
            pin = self.Mux.get_pin(self.MUX_PINS[ind])
            time.sleep(0.1)
            pin.switch_to_output(value=val)
            #print(f"switching pin {ind}")
        self._gain = gain

    @property
    def voltage(self):
        """Get the output voltage of the soft DAC based on the current gain setting."""
        return self.gain_voltages[self._gain]


class Channel:
    """Represents a single control channel on a board, capable of performing MPP tracking.

    Attributes:
        board (OBoard): The parent board that this channel belongs to.
        dac (device): The DAC device associated with this channel.
        ind (int): The index of the channel on the board.
        id (str): Unique identifier for the channel.
        last_v (float): Last recorded voltage.
        last_dir (int): The direction of last voltage change (1 for increase, -1 for decrease).
        last_p (float): Last recorded power.
        dv (float): Step change in voltage during MPP tracking.
        max_dv (float): Maximum allowable change in voltage per step.
        gain_v (int): Gain setting for voltage measurement.
        gain_c (int): Gain setting for current measurement.
    """
    def __init__(self, board, Dac, ind, R_shunt = 20, Voltage_limits=(-1.5,2.5)):
        """Initialize a channel with specific board, DAC, and index."""
        self.board = board
        self.dac = Dac
        self.ind = ind
        self.id = f"{board.ID}channel_{ind}"
        self.R_shunt = R_shunt
        self.Voltage_limits = Voltage_limits
        self.dac.gain=1
        
        # Initialize MPPT tracking variables
        self.last_v = 0.0  # Starting voltage should be at 0 to stay in jsc
        self.last_dir = 1
        self.last_p = 0
        self.dv = 0.05
        self.max_dv = 0.2  # Maximum change in voltage per step

        self.last_jsc  = 0 # The Last JSC measured for this cell
        self.last_voc = 0.5 # The Last VOC measured fot this cell 
        self.time_last_JV = 0 

        # Initialize gain settings
        self.gain_v = 2
        self.gain_c = 8

    def set_voltage(self, voltage):
        """Set the voltage of the DAC to a specific value."""
        voltage_ = min(max(self.Voltage_limits[0], voltage), self.Voltage_limits[1]) + 0.586 # sdac value
        self.dac.value = int((voltage_/4/2*2**16*2))
        #self.dac.value = int(20 * 1e3 * voltage / 100 * 1.0)

    def read_voltage(self):
        """Read the voltage from the ADC after selecting the appropriate channel."""
        self.board.aMux_select_channel(self.ind)
        time.sleep(0.1)  # Short delay for stabilization
        ads = self.board.Adc
        time.sleep(0.1)
        ads.gain = self.gain_v
        time.sleep(0.1)
        V_cell = AnalogIn(ads, 0, 1)
        time.sleep(0.1)
        return V_cell.voltage

    def read_current(self):
        """Read the current from the ADC after selecting the appropriate channel."""
        self.board.aMux_select_channel(self.ind)
        time.sleep(0.1)  # Short delay for stabilization
        ads = self.board.Adc
        time.sleep(0.1)
        ads.gain = self.gain_c
        time.sleep(0.1)
        shnt = AnalogIn(ads, 2, 3)
        time.sleep(0.1)
        return shnt.voltage/self.R_shunt

    def read_voltage_and_current(self):
        """Read both voltage and current from the ADC."""
        voltage = self.read_voltage()
        current = self.read_current()
        return voltage, current

    def mpp_track(self, DATA,cell = None):
        """Track measurements and write them to a CSV file with a maximum dv step.

        Args:
            iterations (int): Number of iterations to run the tracking.
            interval (float): Time between iterations (in seconds).
        """
        # Only run JV if last JV was long enough ago or doesn't exist yet
        if (
            (time.time()- cell.timestamp_last_JV) > DATA.interval_next_JV
        ):
            v_set,v,c = self.JV_Sweep(DATA, cell)
            cell.timestamp_last_JV = time.time()
            time.sleep(0.1)
            #after a JV scan, the cell voltage must be set back to v_mpp
            self.set_voltage(self.last_v)
            time.sleep(0.1)
            # only the first time this jv is run:
            if not cell.initialized:
                set_voltage_max_power, voltage_max_power, _ = get_mpp_from_j_v_data(v_set,v,c)
                voltage_to_set = set_voltage_max_power #voltage vpp - 50mV
                self.last_v = voltage_to_set
                self.set_voltage(voltage_to_set)
                print(f"initialized cell: {cell.id} with a voltage of {voltage_max_power}, set voltage {voltage_to_set}")
                cell.initialized = True


        # Define the file name
        cell_id = cell.id
        iterations = DATA.BOARD_DEFAULT_ITERATIONS
        interval = DATA.BOARD_DEFAULT_INTERVAL

        create_folder_if_not_exists(os.path.join(DATA.local_folder,"TRACKING_DATA"))   
        local_file_path_mpp_data = os.path.join(DATA.local_folder,"TRACKING_DATA",f"CELL{cell_id}_data.csv") 

        # Write the header if the file doesn't exist
        if not os.path.exists(local_file_path_mpp_data):
            with open(local_file_path_mpp_data, 'a') as f:
                f.write('timestamp,measured_voltage,measured_current,dac_value,adc_gain_v,adc_gain_c\n')

        for _ in range(iterations):
            timestamp = datetime.now().isoformat()
            try:
                measured_voltage = self.read_voltage()
                measured_current = self.read_current()
            except Exception as e:
                print(f"Error reading voltage or current: {e}")
                continue

            dac_value = self.dac.raw_value
            curr_p = measured_voltage * measured_current
            #print(f"{measured_voltage} V,{measured_current*1e3}mA,{curr_p*1e3}mW,{self.dac.raw_value}")

            # Write the current data to the CSV file
            with open(local_file_path_mpp_data, 'a') as f:
                f.write(f'{timestamp},{measured_voltage},{measured_current},{dac_value},{self.gain_v},{self.gain_c}\n')


            #write the data to the corresponing directory on the network drive
            network_folder_path_mpp_data = os.path.join(DATA.network_folder, "TRACKING_DATA")
            create_folder_if_not_exists(network_folder_path_mpp_data)
            copy_to_network_drive_gio(local_file_path_mpp_data, network_folder_path_mpp_data)

            if self.last_p < curr_p:
                self.dv = min(self.dv * 1.1, self.max_dv)
            else:
                #print("FLIP")
                self.dv = min(self.dv * 0.3, self.max_dv)
                self.last_dir *= -1
            self.dv = max(2e-3, self.dv)
            #print(f"{self.dv * self.last_dir} dV")
            self.last_v += + self.dv * self.last_dir  # Update voltage
            self.set_voltage(self.last_v)  # Apply adjusted voltage

            self.last_p = curr_p
            time.sleep(interval)

    
    def JV_Sweep(self, DATA, cell):
        cell_id = cell.id
        upper_voltage_limit = cell.voltage_limits_JV[1]
        lower_voltage_limit = cell.voltage_limits_JV[0]
        max_allowed_current =  cell.max_allowed_current
        stepsize = DATA.stepsize_JV
        settle_time = DATA.settletime_JV
        
        create_folder_if_not_exists(os.path.join(DATA.local_folder, "JV_DATA"))
        local_file_path = os.path.join(DATA.local_folder, "JV_DATA", f"CELL{cell_id}_JV_data.csv")

        if not os.path.exists(local_file_path):
            with open(local_file_path, 'w') as f:
                f.write('timestamp,set_voltage,measured_voltage,measured_current,dac_value,adc_gain_v,adc_gain_c\n')

        sweep_voltages = np.arange(lower_voltage_limit, upper_voltage_limit + stepsize, stepsize)
        sweep_voltages = np.concatenate([sweep_voltages, sweep_voltages[::-1]])

        threshold_voltage = 1000#high value

        voltages_meas = []
        curents_meas = []
        set_voltages = []

        for voltage in sweep_voltages:

            if voltage > threshold_voltage: continue

            try:
                print(voltage)
                self.set_voltage(voltage)
                
                #time.sleep(settle_time)
                measured_voltage = self.read_voltage()
                measured_current = self.read_current()

                set_voltages.append(voltage)
                voltages_meas.append(measured_voltage)
                curents_meas.append(measured_current)

            except Exception as e:
                print(f"Error during JV read: {e}")
                continue

            # Sicherheitsabbruch bei zu hohem Strom
            if abs(measured_current) > max_allowed_current:
                threshold_voltage = voltage
                print(f"Abbruch: {measured_current:.3f} A > {max_allowed_current} A bei {voltage:.2f} V")
                
            with open(local_file_path, 'a') as f:
                f.write(f'{datetime.now().isoformat()},{voltage},{measured_voltage},{measured_current},{self.dac.raw_value},{self.gain_v},{self.gain_c}\n')

        # Netzwerk-Export
        network_folder = os.path.join(DATA.network_folder, "JV_DATA")
        create_folder_if_not_exists(network_folder)
        copy_to_network_drive_gio(local_file_path, network_folder)

        return np.array(set_voltages), np.array(voltages_meas), np.array(curents_meas)

def initialize_boards(Data_Measurement):

    # I2C-Adresse des TCA9548A (Standard: 0x70)
    TCA9548A_ADDR = 0x70

    # I2C-Bus initialisieren (für Raspberry Pi: Bus 1 verwenden)
    bus = smbus2.SMBus(1)

    involved_TCA_Channels = []
    for chuck in Data_Measurement.string_chucks:
        for substrate in chuck.substrates: 
            for cell in substrate.cells:
                involved_TCA_Channels.append(cell.TCA_Channel)
    
    involved_TCA_Channels = set(involved_TCA_Channels)

    Data_Measurement.oboard_managers = [None] * 8

    print("Start Scan with TCA9548A...")
    for channel in involved_TCA_Channels:
        print(f"================ Channel {channel}")
        select_channel(channel)
        Data_Measurement.oboard_managers[channel] = OBoardManager(i2c_num=1)

    
    # Alle Kanäle deaktivieren (optional)
    bus.write_byte(TCA9548A_ADDR, 0x00)
    print("Scan complete.")

def select_channel(channel):
    # I2C-Adresse des TCA9548A (Standard: 0x70)
    TCA9548A_ADDR = 0x70
    bus = smbus2.SMBus(1)
    """Wählt den angegebenen TCA9548A-Kanal aus (0–7)."""
    if 0 <= channel <= 7:
        bus.write_byte(TCA9548A_ADDR, 1 << channel)
        time.sleep(0.1)  # Kleine Verzögerung
    else:
        raise ValueError("Kanal muss zwischen 0 und 7 sein")
    
def Blink(substrate,Data_Measurement):
    for cell in substrate.cells:
                
        select_channel(cell.TCA_Channel)
        corresponding_manager = Data_Measurement.oboard_managers[cell.TCA_Channel]
        corresponding_oboard = corresponding_manager.oboards[cell.Octoboard_number]
        corresponding_channel = corresponding_oboard.channel[cell.Channel]


        try:
            print(f"Blinking on channel {cell.Channel} of board {cell.Octoboard_number}")
            for i in range (2):
                corresponding_channel.set_voltage(2)
                time.sleep(0.1)
                print(corresponding_channel.read_voltage())
                time.sleep(0.1)
                corresponding_channel.set_voltage(0)
                time.sleep(0.1)
                #print(corresponding_channel.read_voltage())
        except Exception as e:
            print(f"Error during blinking on channel {cell.Channel} of board {cell.Octoboard_number}: {e}")