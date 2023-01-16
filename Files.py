"""Contains functions related to working with files. Only dependencies should be stuff in Utils.py,
and stuff in this same file."""

import os
import os.path
import json
import time
from typing import Optional
from copy import deepcopy
import shutil
import ntpath

import Utils

_IGN_UUID_PAIRS: Optional[dict] = None

def write_data_as_json_to_file(data: dict, description: str, folder_name: str = "results") -> None:
    filename = create_file(description, folder_name)
    with open(filename, "w") as f:
        f.write(json.dumps(data, indent=4))

def create_file(description: str, folder_name: str) -> str:
    """Creates a file using the params and returns the name of the file, which can be used by the caller if desired."""
    filename = os.path.join(folder_name, Utils.trim_if_needed(description + " - " + str(time.time_ns()) + ".txt"))
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    return filename

def ign_uuid_pairs_in_uuids_txt() -> dict:
    """Retrieves pairs stored in the uuids.txt file as a dict - key ign, value uuid"""
    global _IGN_UUID_PAIRS
    if _IGN_UUID_PAIRS is not None:
        return deepcopy(_IGN_UUID_PAIRS)

    _IGN_UUID_PAIRS = {} # key ign, value uuid
    if not os.path.isfile('uuids.txt'):
        return deepcopy(_IGN_UUID_PAIRS)
    with open('uuids.txt') as file:
        for line in file:
            words = line.rstrip().split()
            _IGN_UUID_PAIRS[words[0].lower()] = words[1]
    return deepcopy(_IGN_UUID_PAIRS)

def read_json_textfile(filepath: str) -> dict:
    try:
        with open(filepath, 'r') as f:
            return json.loads(f.read())
    except FileNotFoundError:
        # This could happen if the user gives a windows path when running the program with wsl. So try this:
        with open('results/' + ntpath.basename(filepath), 'r') as f:
            return json.loads(f.read())

def update_uuids_file(ign_uuid_pairs: dict[str, str]) -> None:
    """Updates the uuids.txt file with the ign_uuid_pairs param. 
    If a uuid is found for an ign in uuids.txt that conflicts with a pair in the passed in param,
    it will be replaced. Also, this function will make a backup of uuids.txt before overwriting it."""

    shutil.copy('uuids.txt', create_file('uuids copy', 'old-uuids'))
    pairs = ign_uuid_pairs_in_uuids_txt()
    pairs.update(ign_uuid_pairs)
    with open("uuids.txt", "w") as file:
        for key, value in pairs.items():
            file.write(key + " " + value + "\n")
            assert key == key.lower()
    print("uuids.txt now contains uuid-ign pairs for " + str(len(pairs)) + " players.")