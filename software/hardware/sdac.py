from .constants import (
    SOFTDAC_MUX_PINS,
    SOFTDAC_DEFAULT_VREF,
    SOFTDAC_GAIN_VOLTAGES,
    SOFTDAC_GAIN_REGISTERS
)

class Softdac:
    """Software-driven DAC implementation using multiplexer for gain control.
    
    This class implements a software-controlled Digital-to-Analog Converter using
    a multiplexer for gain control. It provides multiple gain levels with 
    corresponding voltage outputs.
    
    Attributes:
        mux: Multiplexer device instance for pin control
        vref (float): Reference voltage in volts
        _gain (int): Current gain setting
        
    Constants:
        SOFTDAC_MUX_PINS: List of multiplexer pins used for gain control
        GAIN_VOLTAGES: Array of voltage levels for each gain setting
        GAIN_REGISTERS: Array of pin configurations for each gain level
    """
    
    def __init__(self, mux_device, vref=SOFTDAC_DEFAULT_VREF):
        """Initialize the Softdac.
        
        Args:
            mux_device: Multiplexer device instance for pin control
            vref (float, optional): Reference voltage in volts. Defaults to DEFAULT_VREF.
        """
        self.mux = mux_device
        self.vref = vref
        self._gain = 0

    @property
    def gain(self):
        """Get the current gain setting.
        
        Returns:
            int: Current gain level
        """
        return self._gain

    @gain.setter
    def gain(self, gain: int):
        """Set the gain level.
        
        Args:
            gain (int): Desired gain level
            
        Raises:
            ValueError: If gain value is outside the valid range
        """
        if gain < 0 or gain >= len(SOFTDAC_GAIN_VOLTAGES):
            raise ValueError(
                f"Invalid gain value. Must be between 0 and {len(SOFTDAC_GAIN_VOLTAGES)-1}"
            )
        self._set_gain_pins(gain)
        self._gain = gain

    def _set_gain_pins(self, gain):
        """Set multiplexer pins for the specified gain level.
        
        Args:
            gain (int): Desired gain level
        """
        pin_values = SOFTDAC_GAIN_REGISTERS[gain]
        for pin, value in zip(SOFTDAC_MUX_PINS, pin_values):
            self.mux.set_pin(pin, bool(value))

    @property
    def voltage(self):
        """Get the output voltage for the current gain setting.
        
        Returns:
            float: Output voltage in volts
        """
        return SOFTDAC_GAIN_VOLTAGES[self._gain]