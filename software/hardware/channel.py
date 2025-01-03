from .constants import *
import os
import time
from datetime import datetime
from adafruit_ads1x15.analog_in import AnalogIn

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

    def __init__(self, board, Dac, ind, R_shunt=CHANNEL_DEFAULT_SHUNT_RESISTANCE, 
                 Voltage_limits=CHANNEL_VOLTAGE_LIMITS):
        """Initialize a channel with specific board, DAC, and index."""
        self.board = board
        self.dac = Dac
        self.ind = ind
        self.id = f"{board.ID}channel_{ind}"
        self.R_shunt = R_shunt
        self.Voltage_limits = Voltage_limits
        self.dac.gain = CHANNEL_DAC_GAIN
        
        # Initialize MPPT tracking variables
        self.last_v = CHANNEL_INITIAL_VOLTAGE
        self.last_dir = CHANNEL_INITIAL_DIRECTION
        self.last_p = CHANNEL_INITIAL_POWER
        self.dv = CHANNEL_INITIAL_VOLTAGE_STEP
        self.max_dv = CHANNEL_MAX_VOLTAGE_STEP

        # Initialize gain settings
        self.gain_v = CHANNEL_VOLTAGE_GAIN
        self.gain_c = CHANNEL_CURRENT_GAIN

    def set_voltage(self, voltage):
        """Set the voltage of the DAC to a specific value."""
        voltage_ = min(max(self.Voltage_limits[0], voltage), self.Voltage_limits[1])
        self.dac.value = int(voltage_ * CHANNEL_DAC_VOLTAGE_SCALE)

    def read_voltage(self):
        """Read the voltage from the ADC after selecting the appropriate channel."""
        self.board.aMux_select_channel(self.ind)
        time.sleep(CHANNEL_ADC_SETTLE_TIME)
        ads = self.board.Adc
        ads.gain = self.gain_v
        V_cell = AnalogIn(ads, 0, 1)
        return V_cell.voltage

    def read_current(self):
        """Read the current from the ADC after selecting the appropriate channel."""
        self.board.aMux_select_channel(self.ind)
        time.sleep(CHANNEL_ADC_SETTLE_TIME)
        ads = self.board.Adc
        ads.gain = self.gain_c
        shnt = AnalogIn(ads, 2, 3)
        return shnt.voltage / self.R_shunt

    def mpp_track(self, iterations=10, interval=0.01):
        """Track measurements and write them to a CSV file with a maximum dv step.

        Args:
            iterations (int): Number of iterations to run the tracking.
            interval (float): Time between iterations (in seconds).
        """
        file_name = os.path.join(CHANNEL_DATA_DIRECTORY, f'{self.id}_data.csv')
        os.makedirs(CHANNEL_DATA_DIRECTORY, exist_ok=True)

        if not os.path.exists(file_name):
            with open(file_name, 'a') as f:
                f.write(f'{CHANNEL_DEFAULT_HEADER}\n')

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

            with open(file_name, 'a') as f:
                f.write(f'{timestamp},{measured_voltage},{measured_current},'
                       f'{dac_value},{self.gain_v},{self.gain_c}\n')

            # Update step size based on power change
            if self.last_p < curr_p:
                self.dv = min(self.dv * CHANNEL_POWER_INCREASE_FACTOR, self.max_dv)
            else:
                self.dv = min(self.dv * CHANNEL_POWER_DECREASE_FACTOR, self.max_dv)
                self.last_dir *= -1
            self.dv = max(CHANNEL_MIN_VOLTAGE_STEP, self.dv)

            self.last_v += self.dv * self.last_dir
            self.set_voltage(self.last_v)
            self.last_p = curr_p
            time.sleep(interval)

    def perform_iv_sweep(self, start_value=CHANNEL_IV_START_VALUE, 
                        end_value=CHANNEL_IV_END_VALUE,
                        step_size=CHANNEL_IV_STEP_SIZE):
        """Performs an IV sweep from a start value to an end value on the DAC."""
        file_name = os.path.join(CHANNEL_IV_DIRECTORY, f'{self.id}_data.csv')
        os.makedirs(CHANNEL_IV_DIRECTORY, exist_ok=True)

        with open(file_name, 'w') as f:
            f.write(f'{CHANNEL_DEFAULT_HEADER}\n')

        for dac_value in range(start_value, end_value + 1, step_size):
            self.set_voltage(dac_value)
            time.sleep(CHANNEL_ADC_SETTLE_TIME)
            voltage = self.read_voltage()
            current = self.read_current()
            dac_value = self.dac.raw_value
            timestamp = datetime.now().isoformat()
            
            with open(file_name, 'a') as f:
                f.write(f'{timestamp},{voltage},{current},'
                       f'{dac_value},{self.gain_v},{self.gain_c}\n')
                
        self.set_voltage(0)