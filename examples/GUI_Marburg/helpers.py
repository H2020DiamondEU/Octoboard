from Data_Classes import Data_Measurement
import yaml
#from drivers.constants import *
from Data_Classes import Data_Measurement

import subprocess
import os
import numpy as np
import os
from pydantic import BaseModel
import yaml
import matplotlib.pyplot as plt
from collections import OrderedDict

def load_measurement_from_yaml(path: str) -> Data_Measurement:
    # Custom YAML loader that preserves order
    class OrderedLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping
    )

    with open(path, "r") as file:
        raw_data = yaml.load(file, Loader=OrderedLoader)

    return Data_Measurement(**raw_data)

def copy_to_network_drive_gio(source_filepath, target_folder, timeout_seconds=10):
    try:
        filename = os.path.basename(source_filepath)
        target_filepath = f"{target_folder}/{filename}"

        subprocess.run(
            ["gio", "copy", source_filepath, target_filepath],
            check=True,
            timeout=timeout_seconds
        )
        # print(f"Datei erfolgreich mit gio kopiert nach:\n{target_filepath}")
    except subprocess.TimeoutExpired:
        print(f"Fehler: Kopiervorgang hat das Zeitlimit von {timeout_seconds} Sekunden überschritten.")
    except Exception as e:
        print(f"Fehler beim Kopieren auf das Netzwerklaufwerk mit gio: {e}")


def export_yaml(data_object: BaseModel, filepath: str) -> None:
    """
    Exportiert eine Pydantic-Datenklasse als YAML-Datei.

    :param data_object: Ein Pydantic-Objekt (z. B. Data_Measurement)
    :param filepath: Pfad zur Zieldatei (inklusive .yaml oder .yml)
    """
    with open(filepath, 'w') as file:
        yaml.dump(data_object.dict(exclude={"oboard_managers"}), file, sort_keys=False, allow_unicode=True)
        print(f"saved settings yaml to {filepath}")


def create_folder_if_not_exists(path: str) -> None:
    """
    Erstellt ein Verzeichnis, wenn es noch nicht existiert.

    :param path: Der Pfad zum gewünschten Verzeichnis
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError as e:
        print(f"Fehler beim Erstellen des Verzeichnisses '{path}': {e}")


def get_mpp_from_j_v_data(v_set,v, c):
    p_jv = v * c
    valid_mask = (v > 0) & (c > 0)
    
    if not np.any(valid_mask):
        print("No valid data points with v > 0 and c < 0.")
        p_valid = p_jv
        v_valid = v
        c_valid = c
        v_set_valid = v_set
    else: 
        p_valid = p_jv[valid_mask]
        v_valid = v[valid_mask]
        c_valid = c[valid_mask]
        v_set_valid = v_set[valid_mask]

    idx_max_power = np.argmax(p_valid)  # most negative value
    voltage_max_power = v_valid[idx_max_power]
    current_max_power = c_valid[idx_max_power]
    voltage_set_max_power = v_set_valid[idx_max_power]

    return voltage_set_max_power,voltage_max_power, current_max_power
