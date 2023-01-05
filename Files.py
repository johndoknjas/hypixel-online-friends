"""Contains functions related to working with files. Only dependencies should be stuff in Utils.py,
and stuff in this same file."""

import os
import os.path
import json
import time
import Utils
from typing import Optional
from copy import deepcopy

_IGN_UUID_PAIRS: Optional[dict] = None

def write_data_as_json_to_file(data: dict, description: str = "") -> None:
    filename = os.path.join("results", Utils.trim_if_needed(description + " - " + str(time.time_ns()) + ".txt"))
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(json.dumps(data, indent=4))

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

def get_all_jsons_in_results() -> list[dict]:
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