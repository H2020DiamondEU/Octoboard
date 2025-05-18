from pydantic import BaseModel, Field
from typing import Literal, Dict, Optional, List, Any
from pydantic import BaseModel, Field, PrivateAttr
import yaml
from datetime import datetime
from typing import Optional

#####################################
# Level 3: Class for general information of the Cell
class Data_Cell(BaseModel):
    """
        Level 3: Class for general information of the Substrate
    """
    id: str  # number between 0 and 255
    TCA_Channel: int  # number between 0 and 7
    Octoboard_number: int  # number between 0 and 3
    Channel: int  # number between 0 and 7
    max_allowed_current: float = 0.05
    voltage_limits_JV: List[float] = [-0.3,1.25] 
    timestamp_last_JV: int = 0 # linux time in seconds of the last JV
    Last_JSC: float  = 0 # The Last JSC measured for this cell
    Last_VOC: float = 0.5 # The Last VOC measured fot this cell 
    initialized: bool = False

# Level 2: Class for general information of the Substrate
class Data_Substrate(BaseModel):
    """
        Level 2: Class for general information of the Substrate
    """
    id: str  # Every substrate has an ID
    batch_number: str  # Every substrate has a Batch Number
    type: Literal["MR", "EPFL","Sensor_Device", "Resistor"]  # Every substrate has a Type (either MR or EPFL)
    active: bool = True
    number_of_cells: int = Field(default=4)  # Every substrate has a number of cells (in case of MR it is 4, in case of EPFL it is 1)
    icon: Literal["Empty_Substrate_Slot.png", "UMR_Cell_Design.png", "EPFL_Cell_Design.png", "Resistor.png", "Sensor_Device.png"]
    cells: List[Data_Cell]  # here we will have cell objects
    slot_index: Optional[int] = None

# Level 1: Class for general information of the String Chuck
class Data_String_Chuck(BaseModel):
    """
    Level 1: Class for general information of the String Chuck
    """
    id: str  # Default to a placeholder string
    type: Literal["MR", "EPFL"] = None  # Default to "None"
    icon: Literal["Empty_Slot.png", "String_Chuck_MR.png", "String_Chuck_EPFL.png"] = "Empty_Slot.png"  # Default to empty slot
    cell_slots: int = 0
    active: bool = False  # Default to not installed
    installed_cells: Dict[int, Optional[Data_Substrate]] = Field(default_factory=dict)  # Default to empty dictionary
    position: int = 0  # Default position is 0
    relative_substrate_positions: List[float] = []  # Center of the substrates relative to the top of the chucks
    substrates: List[Data_Substrate] = []  # This is an empty list of substrate positions

    class Config:
        arbitrary_types_allowed = True


# Level 0: Class for general information of the Measurement
class Data_Measurement(BaseModel):
    """
    Level 0: Class for general information of the Measurement
    """
    id: str
    string_chucks: List[Data_String_Chuck]  # <- jetzt Liste von Objekten
    user: str
    local_folder: str
    network_folder: str
    oboard_managers: List = []#Optional[List[OBoardManager]] = PrivateAttr(default=[])
    # each measurment has a list of OBoardManagers which can be accesed.
    mpp_algorithm: Literal[
        "PERTURB_AND_OBSERVE"
    ]
    CHANNEL_POWER_INCREASE_FACTOR: float = 1.1 # Factor to increase step size when power increases
    CHANNEL_POWER_DECREASE_FACTOR: float = 0.3 # Factor to decrease step size when power decreases
    BOARD_DEFAULT_ITERATIONS:int = 10
    BOARD_DEFAULT_INTERVAL:float = 0.001  # seconds
    stepsize_JV :float = 0.045 #Volt
    settletime_JV : float= 0.1 # seconds dont change
    interval_next_JV: int = 10000 # Perform a JV-SCan after a certain amunt of seconds


    

 