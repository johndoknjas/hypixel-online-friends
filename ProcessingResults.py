"""Contains functions for dealing with reading from the results folder.
   No file (except main.py) should depend on this file, and this file should ideally not depend
   on much in other files. This will make things easier if this file ends up being rewritten in C++ later on. """

import os
import os.path
from typing import Optional, List
from copy import deepcopy

import Utils
import Files
from Player import Player
from MyClasses import UUID_Plus_Time
import hypixel

_all_dicts_unique_uuids: Optional[list[dict]] = None
_ign_uuid_pairs_in_results: Optional[dict[str, str]] = None
_player_uuids_with_f_list_in_results: Optional[List[str]] = None

def ign_uuid_pairs_in_results(get_deepcopy: bool = False) -> dict[str, str]:
    global _ign_uuid_pairs_in_results

    if not _ign_uuid_pairs_in_results:
        _ign_uuid_pairs_in_results = {}
        for d in get_all_dicts_unique_uuids_in_results():
            _ign_uuid_pairs_in_results.update(Utils.get_all_ign_uuid_pairs_in_dict(d))
    return deepcopy(_ign_uuid_pairs_in_results) if get_deepcopy else _ign_uuid_pairs_in_results

def check_results(player: Optional[Player]) -> List[str]:
    """Traverses through the results folder and prints some stats and info. If a Player object is provided
    for player, then some specific info about them will be outputted as well."""
    global _player_uuids_with_f_list_in_results

    all_dicts: list[dict] = get_all_dicts_unique_uuids_in_results()

    print("\n" + str(len(all_dicts)) + " total unique uuids recorded in the results folder.")
    keys = ['friends', 'name', 'fkdr', 'star']
    all_dicts = [d for d in all_dicts if any(k in d for k in keys)]
    print(str(len(all_dicts)) + " total players with non-trivial data stored in the results folder.")

    for k in keys:
        dicts_with_key = [d for d in all_dicts if k in d]
        indent = "  "
        Utils.print_info_for_key(dicts_with_key, k, indent)
        if k != 'friends':
            continue
        _player_uuids_with_f_list_in_results = [d['uuid'] for d in dicts_with_key]
        if player:
            print(indent*2 + "Also, it's " + 
                  Utils.bool_lowercase_str(player.uuid() in _player_uuids_with_f_list_in_results) +
                  " that " + player.name() + "'s friends list is in the results folder.")
    print('\n\n')

def player_uuids_with_f_list_in_results(get_deepcopy: bool = False) -> List[str]:
    global _player_uuids_with_f_list_in_results

    if not _player_uuids_with_f_list_in_results:
        raise ValueError("Probably haven't called the checkresults() function yet.")
    return (deepcopy(_player_uuids_with_f_list_in_results) 
            if get_deepcopy else _player_uuids_with_f_list_in_results)

def get_all_dicts_unique_uuids_in_results(get_deepcopy: bool = False) -> List[dict]:
    """Returns a flat list of dicts (no more than one per uuid), for all dicts/nested dicts found in the 
    results folder. If multiple dicts have the same uuid, the one with the biggest friends list will be kept."""
    global _all_dicts_unique_uuids

    if not _all_dicts_unique_uuids:
        _all_dicts_unique_uuids = []
        for d in _get_all_jsons_in_results():
            _all_dicts_unique_uuids.extend(Utils.get_all_nested_dicts_in_dict(d, make_deepcopy = False))
        _all_dicts_unique_uuids = Utils.remove_dicts_duplicate_uuids(_all_dicts_unique_uuids, 
                                                                     make_deepcopy = False)

    return deepcopy(_all_dicts_unique_uuids) if get_deepcopy else _all_dicts_unique_uuids

def get_largest_f_list_for_player_in_results(ign_or_uuid: str) -> List[UUID_Plus_Time]:
    if not Utils.is_uuid(ign_or_uuid):
        ign_or_uuid = hypixel.get_uuid_from_textfile_if_exists(ign_or_uuid)
    for d in get_all_dicts_unique_uuids_in_results():
        if d['uuid'] == ign_or_uuid or d.get('name', None) == ign_or_uuid:
            return [UUID_Plus_Time(f['uuid'], f.get('time', None)) for f in d.get('friends', [])]
    return []

def _get_all_jsons_in_results() -> List[dict]:
    """Returns a list of dicts, where each dict represents the json each textfile stores."""
    all_jsons: list[dict] = []
    all_files = os.listdir('results')
    all_files = [f for f in all_files if f.startswith('Friends of') and f.endswith('.txt')]
    for f in all_files:
        filename = os.path.join('results', f)
        all_jsons.append(Files.read_json_textfile(filename))
    return all_jsons
