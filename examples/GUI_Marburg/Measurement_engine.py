from Data_Classes import Data_Measurement
from old_drivers import select_channel

# chatgpt --> this shall be executed until the measurement is stopped 
def track(Data_Measurement: Data_Measurement):
    for string_chuck in sorted(Data_Measurement.string_chucks, key = lambda c: int(c.id)): 
            if not string_chuck.active: continue
            for substrate in sorted(string_chuck.substrates, key=lambda c: int(c.id)):
                if  not substrate.active: continue
                for cell in sorted(substrate.cells, key=lambda c: int(c.id)):

                    select_channel(cell.TCA_Channel)
                    corresponding_manager = Data_Measurement.oboard_managers[cell.TCA_Channel]
                    corresponding_oboard = corresponding_manager.oboards[cell.Octoboard_number]
                    corresponding_channel = corresponding_oboard.channel[cell.Channel]

                    try:
                        print(f"Tracking on channel {cell.Channel} of board {cell.Octoboard_number}")
                        corresponding_channel.mpp_track(
                           DATA = Data_Measurement, cell = cell
                        )
                    except Exception as e:
                        print(f"Error during MPP tracking on channel {cell.Channel} of board {cell.Octoboard_number}: {e}")


def set_all_cells_to_voltage(Data_Measurement, voltage = 0.5):
    for string_chuck in sorted(Data_Measurement.string_chucks, key = lambda c: c.id): 
            for substrate in sorted(string_chuck.substrates, key=lambda c: c.id):
                for cell in sorted(substrate.cells, key=lambda c: c.id):

                    select_channel(cell.TCA_Channel)
                    corresponding_manager = Data_Measurement.oboard_managers[cell.TCA_Channel]
                    corresponding_oboard = corresponding_manager.oboards[cell.Octoboard_number]
                    corresponding_channel = corresponding_oboard.channel[cell.Channel]
                           
                    try:
                        print(f"Setting {cell.Channel} of board {cell.Octoboard_number} to {voltage}V")
                        corresponding_channel.set_voltage(voltage)
                    except Exception as e:
                        print(f"Error: Could not set {cell.Channel} of board {cell.Octoboard_number} to 0.5V: {e}")