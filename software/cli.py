import argparse
from . import OBoardManager
import time

def main():
    parser = argparse.ArgumentParser(description="Run MPP Tracking on Octoboards")
    parser.add_argument("i2c_nums", type=int, nargs='+', help="List of I2C bus numbers")
    args = parser.parse_args()
    
    board_managers = []
    
    # Initialize all board managers
    for i2c_num in args.i2c_nums:
        print(f"Initializing MPP tracking on I2C bus {i2c_num}")
        board_managers.append(OBoardManager(i2c_num=i2c_num))
        time.sleep(.1)

    # Run operations on each board manager
    for board_manager in board_managers:
        time.sleep(.1)
        for oboard in board_manager.oboards:
            for ch in range(8):
                oboard.channel[ch].perform_iv_sweep()
                    
    iterations = 2
    while True:
        for board_manager in board_managers:
            time.sleep(.1)
            for oboard in board_manager.oboards:
                for ch in range(8):
                    try:
                        oboard.channel[ch].mpp_track(iterations=iterations, interval=1e-4)
                    except Exception as e:
                        print(f"Error during MPP tracking on channel {ch} of board {oboard.ID}: {e}")
        iterations = 4

if __name__ == "__main__":
    main()
    