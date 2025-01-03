from . import ExtendedI2C
from .channel import Channel
from . import Softdac
import adafruit_mcp4728
import adafruit_ads1x15.ads1115 as ADS
from adafruit_mcp230xx.mcp23017 import MCP23017
import numpy as np
import time
from datetime import datetime
from adafruit_blinka.microcontroller.generic_linux.i2c import I2C as _I2C
from adafruit_blinka.microcontroller.generic_linux.spi import SPI as _SPI
from os import path
import threading

from .constants import (
    BOARD_DEFAULT_I2C_NUM,
    I2C_BASE_MUX,
    I2C_BASE_ADC,
    I2C_BASE_DAC_0,
    I2C_BASE_DAC_1,
    I2C_DAC_CHANNELS,
    CHANNELS_PER_BOARD,
    MAX_CHANNELS_PER_DAC,
    I2C_OFFSET_MULTIPLIER,
    CHANNEL_VOLTAGE_GAIN,
    CHANNEL_CURRENT_GAIN,
    CHANNEL_ADC_SETTLE_TIME,
)

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
    
    def __init__(self, i2c_num=BOARD_DEFAULT_I2C_NUM, i2c_address_offset=2, debug=False):
        """Initialize an OBoard with specified I2C pins and address offset."""
        i2c = ExtendedI2C(i2c_num)
        self.i2c_num = i2c_num
        self.debug = debug
        self.ID = f"Bus_{i2c_num}_offset{i2c_address_offset}_"
        
        # Calculate device addresses with offset
        self.i2c_base_address = [
            I2C_BASE_MUX + i2c_address_offset * I2C_OFFSET_MULTIPLIER[I2C_BASE_MUX],
            I2C_BASE_ADC + i2c_address_offset * I2C_OFFSET_MULTIPLIER[I2C_BASE_ADC],
            I2C_BASE_DAC_0 + i2c_address_offset * I2C_OFFSET_MULTIPLIER[I2C_BASE_DAC_0],
            I2C_BASE_DAC_1 + i2c_address_offset * I2C_OFFSET_MULTIPLIER[I2C_BASE_DAC_1]
        ]
        
        self.i2c_base_devices = ["mux", "ADC", "DAC_0", "DAC_1"]
        
        # Initialize devices with calculated addresses
        self.Dac_0 = adafruit_mcp4728.MCP4728(
            i2c, 
            address=I2C_BASE_DAC_0 + i2c_address_offset * I2C_OFFSET_MULTIPLIER[I2C_BASE_DAC_0]
        )
        self.Dac_1 = adafruit_mcp4728.MCP4728(
            i2c, 
            address=I2C_BASE_DAC_1 + i2c_address_offset * I2C_OFFSET_MULTIPLIER[I2C_BASE_DAC_1]
        )
        self.Mux = MCP23017(
            i2c, 
            address=I2C_BASE_MUX + i2c_address_offset * I2C_OFFSET_MULTIPLIER[I2C_BASE_MUX]
        )
        self.Adc = ADS.ADS1115(
            i2c, 
            gain=CHANNEL_VOLTAGE_GAIN,
            data_rate=CHANNEL_CURRENT_GAIN,
            address=I2C_BASE_ADC + i2c_address_offset * I2C_OFFSET_MULTIPLIER[I2C_BASE_ADC]
        )
        self.softdac = Softdac(self.Mux)
        
        # Initialize channels
        self.channel = []
        for ch in range(CHANNELS_PER_BOARD):
            dac = self.Dac_0 if ch < MAX_CHANNELS_PER_DAC else self.Dac_1
            self.channel.append(
                Channel(
                    self,
                    Dac=dac.__dict__[I2C_DAC_CHANNELS[ch % MAX_CHANNELS_PER_DAC]],
                    ind=ch
                )
            )

    def print(self, message):
        """Prints a message if debugging is enabled."""
        if self.debug:
            print(message)

    def aMux_enable(self):
        """Enable the analog multiplexer by setting the control pin low."""
        pin = self.Mux.get_pin(MUX_CONTROL_PIN)
        pin.switch_to_output(value=0)

    def aMux_disable(self):
        """Disable the analog multiplexer by setting the control pin high."""
        pin = self.Mux.get_pin(MUX_CONTROL_PIN)
        pin.switch_to_output(value=1)

    def aMux_select_channel(self, channel: int):
        """Select a specific channel on the multiplexer."""
        if channel < 0 or channel >= CHANNELS_PER_BOARD:
            raise ValueError("Invalid channel number")
        
        time.sleep(CHANNEL_ADC_SETTLE_TIME)  # Allow settling time for channel switch
        
        # Set address bits
        for bit in range(3):  # 3 bits for 8 channels
            val = bool(channel >> bit & 1)
            pin = self.Mux.get_pin(4 + bit)  # Pins 4, 5, 6 used for channel selection
            self.print(f"Setting pin {4 + bit} to {'HIGH' if val else 'LOW'}")
            pin.switch_to_output(value=val)