
from .constants import *
from .oboard import OBoard
from .i2c import ExtendedI2C

class OBoardManager:
    """
    Manages multiple OBoard instances for Maximum Power Point Tracking (MPPT) operations across several I2C boards.
    
    This class handles the initialization, configuration, and operation of multiple OBoards connected via I2C.
    It automatically detects compatible boards on the specified I2C bus and manages their operation for MPPT
    tracking across all channels.

    Attributes:
        oboards (list[OBoard]): List of initialized and configured OBoard instances.
        i2c_num (int): The I2C bus number being used.
        i2c (ExtendedI2C): The I2C interface instance for communication.

    Example:
        >>> manager = OBoardManager(i2c_num=1)
        >>> manager.cycle_all_channels(iterations_per_channel=10)
        >>> manager.print_all_boards_status()

    Note:
        The manager expects boards to have specific I2C devices at predefined addresses:
        - Multiplexer (MCP23017) at base address 32
        - ADC (ADS1115) at base address 72
        - DAC_0 (MCP4728) at base address 96
        - DAC_1 (MCP4728) at base address 97
        
        Each board uses an offset from these base addresses to allow multiple boards
        on the same I2C bus.
    """
    def __init__(self, i2c_num=BOARD_DEFAULT_I2C_NUM, 
                 possible_offsets=BOARD_DEFAULT_OFFSET_RANGE):
        """Initialize the OBoardManager by scanning I2C devices and setting up boards accordingly."""
        self.oboards = []
        self.i2c_num = i2c_num
        self.i2c = ExtendedI2C(i2c_num)
        self.setup_boards(possible_offsets)

    def setup_boards(self, possible_offsets):
        """Scan I2C addresses and initialize boards only if all required devices are detected."""
        while not self.i2c.try_lock():
            pass

        found_devices = set(self.i2c.scan())
        self.i2c.unlock()
        print(f"Found I2C devices at addresses: {found_devices}")

        for offset in possible_offsets:
            expected_device_addresses = set([
                base + (offset * I2C_OFFSET_MULTIPLIER[base])
                for base in I2C_BASE_ADDRESSES
            ])
            if expected_device_addresses.issubset(found_devices):
                try:
                    ob = OBoard(i2c_num=self.i2c_num, i2c_address_offset=offset)
                    self.oboards.append(ob)
                    print(f"Successfully initialized OBoard with I2C offset {offset}")
                except Exception as e:
                    print(f"Failed to initialize board with offset {offset}: {e}")
                    raise e
            else:
                print(f"Not all devices found for board with offset {offset}. "
                      f"Expected {expected_device_addresses}, found {found_devices}")

    def cycle_all_channels(self, iterations_per_channel=BOARD_DEFAULT_ITERATIONS, 
                          interval=BOARD_DEFAULT_INTERVAL):
        """
        Perform MPPT tracking on all channels of all detected boards.

        Cycles through each channel on each board, performing Maximum Power Point
        Tracking for the specified number of iterations.

        Args:
            iterations_per_channel (int, optional): Number of MPPT iterations per channel.
                                                  Defaults to 10.
            interval (float, optional): Time interval between iterations in seconds.
                                      Defaults to 0.001.
        """
        for oboard in self.oboards:
            for channel in oboard.channel:
                channel.mpp_track(iterations=iterations_per_channel, interval=interval)

    def print_all_boards_status(self):
        """Print the status of all boards for debugging purposes."""
        for oboard in self.oboards:
            print(f"Board ID: {oboard.ID}")
            for channel in oboard.channel:
                print(f"Channel ID: {channel.id}, Last Voltage: {channel.last_v}")