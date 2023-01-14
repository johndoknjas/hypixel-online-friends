"""Contains functions related to working with files. Only dependencies should be stuff in Utils.py,
and stuff in this same file."""

import os
import os.path
import json
import time
import Utils
from typing import Optional, List
from copy import deepcopy
import shutil
import ntpath

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

def ign_uuid_pairs() -> dict:
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

def get_all_jsons_in_results() -> List[dict]:
    """Returns a list of dicts, where each dict represents the json each textfile stores."""
    all_jsons: list[dict] = []
    all_files = os.listdir('results')
    all_files = [f for f in all_files if f.startswith('Friends of') and f.endswith('.txt')]
    for f in all_files:
        filename = os.path.join('results', f)
        all_jsons.append(read_json_textfile(filename))
    return all_jsons

def get_all_dicts_unique_uuids_in_results() -> List[dict]:
    """Returns a flat list of dicts (no more than one per uuid), for all dicts/nested dicts found in the 
    results folder. If multiple dicts have the same uuid, the one with the biggest friends list will be kept."""
    all_dicts: list[dict] = []
    for d in get_all_jsons_in_results():
        all_dicts.extend(Utils.get_all_nested_dicts_in_dict(d, make_deepcopy = False))
    return Utils.remove_dicts_duplicate_uuids(all_dicts, make_deepcopy = False)

def update_uuids_file() -> None:
    """Updates the uuids.txt file with new ign-uuid pairs found. 
    uuids.txt should continue to contain no duplicates.
    Note that if a player has changed their ign, and then another player is now using that ign, the existing
    ign-uuid pair for the old player may or may not be overwritten by the new pair in uuids.txt.
    Also, this function will make a backup of uuids.txt before overwriting it."""
    shutil.copy('uuids.txt', create_file('uuids copy', 'old-uuids'))
    pairs = ign_uuid_pairs()
    all_jsons: list[dict] = get_all_jsons_in_results()
    for json in all_jsons:
        pairs.update(Utils.get_all_ign_uuid_pairs_in_dict(json))
    # Due to the nature of the update function, there should be no duplicates in pairs.
    with open("uuids.txt", "w") as file:
        for key, value in pairs.items():
            file.write(key + " " + value + "\n")
            assert key == key.lower()
    print("uuids.txt now contains uuid-ign pairs for " + str(len(pairs)) + " players.")