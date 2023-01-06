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

def get_uuid(uuid_or_ign) -> str:
    """If a uuid is passed in, it'll simply be returned. Otherwise if it's an ign, a uuid will be returned if
    a pair for it exists. Otherwise, the ign just gets returned."""
    return ign_uuid_pairs().get(uuid_or_ign, uuid_or_ign)

def read_json_textfile(relative_filepath: str) -> dict:
    with open(relative_filepath, 'r') as f:
        dict_from_file = json.loads(f.read())
    return dict_from_file

def get_all_jsons_in_results() -> List[dict]:
    """Returns a list of dicts, where each dict represents the json each textfile stores."""
    all_jsons: list[dict] = []
    all_files = os.listdir('results')
    all_files = [f for f in all_files if f.startswith('Friends of') and f.endswith('.txt')]
    for f in all_files:
        filename = os.path.join('results', f)
        all_jsons.append(read_json_textfile(filename))
    return all_jsons

def num_players_with_f_lists_in_results() -> int:
    """Returns the number of unique players who have their f lists stored in the results folder."""
    all_jsons: list[dict] = get_all_jsons_in_results()
    all_players_with_f_list_in_results: list[str] = []
    for json in all_jsons:
        all_players_with_f_list_in_results.extend(Utils.get_all_players_with_f_list_in_dict(json))
    return len(Utils.remove_duplicates(all_players_with_f_list_in_results))

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