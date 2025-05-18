from Data_Classes import Data_Cell, Data_Substrate, Data_String_Chuck, Data_Measurement
import yaml
from pydantic import BaseModel, Field
from typing import Literal, Dict, Optional, List, Union
import os

# Global counter
global_cell_id = 0


def generate_cells(n: int, start_id: int) -> List[Data_Cell]:
    return [
        Data_Cell(
            id=str(start_id + i),
            TCA_Channel= 7 - ((start_id + i) // 32),
            Octoboard_number=((start_id + i) // 8) % 4,
            Channel=(start_id + i) % 8
        )
        for i in range(n)
    ]


def generate_substrate(sub_id: int, substrate_type: str, cell_id_counter: int, slot_index: int) -> (Data_Substrate, int):
    n_cells = 4 if substrate_type == "MR" else 1
    cells = generate_cells(n_cells, cell_id_counter)
    substrate = Data_Substrate(
        id=str(sub_id),
        batch_number="Batch_01",
        type=substrate_type,
        number_of_cells=n_cells,
        icon="UMR_Cell_Design.png" if substrate_type == "MR" else "EPFL_Cell_Design.png",
        cells=cells,
        slot_index=slot_index,  # <<< NEU: Speichern auf welchem Platz der Substrat sitzt
    )
    return substrate, cell_id_counter + n_cells




def generate_string_chuck(index: int, chuck_type: str, cell_id_counter: int) -> (Data_String_Chuck, int):
    n_substrates = 10 if chuck_type == "MR" else 16

    # Positionen vorher berechnen
    if chuck_type == "MR":
        relative_positions = [1 - 42 / 500 - 30 / 500 * k for k in reversed(range(10))]
    else:
        relative_positions = [1 - 42 / 500 - 21 / 500 * k for k in reversed(range(16))]

    substrates = []
    for local_idx in range(n_substrates):
        substrate_id = index * n_substrates + local_idx
        substrate, cell_id_counter = generate_substrate(substrate_id, chuck_type, cell_id_counter, local_idx)
        substrates.append(substrate)


    chuck = Data_String_Chuck(
        id=str(index),
        type=chuck_type,
        icon="String_Chuck_MR.png" if chuck_type == "MR" else "String_Chuck_EPFL.png",
        substrates=substrates,
        cell_slots=len(substrates) * (4 if chuck_type == "MR" else 1),
        active=True,
        installed_cells={},
        position=index,
        relative_substrate_positions=relative_positions,  # bleibt drin, falls du noch leere Plätze tracken willst
    )

    return chuck, cell_id_counter




def create_measurement_structure() -> dict:
    string_chucks = []
    cell_id_counter = 0

    # Add 1 EPFL Chuck
    chuck, cell_id_counter = generate_string_chuck(0, "EPFL", cell_id_counter)
    string_chucks.append(chuck)


    # Add 6 MR Chucks
    for i in range(1,3):
        chuck, cell_id_counter = generate_string_chuck(i, "MR", cell_id_counter)
        string_chucks.append(chuck)

    

    # Measurement object
    measurement = Data_Measurement(
        id="Measurement_001",
        string_chucks=string_chucks,  # <-- jetzt als Liste
        user="Test_User",
        local_folder="DATA",
        network_folder = "/run/user/1000/gvfs/smb-share:server=vsrz001.hrz-services.uni-marburg.de,share=physik_k$/solar/5_ScientificResults/03_CharacterizationDevelopment/DATA_MPP",
        mpp_algorithm="PERTURB_AND_OBSERVE"
    )

    return measurement.dict()  # .dict() macht es yaml-kompatibel



# Save to YAML
with open(os.path.join("DATA","settings.yaml"), "w") as f:
    yaml.dump(create_measurement_structure(), f, sort_keys=False)

print("YAML file 'measurement_structure.yaml' created.")
