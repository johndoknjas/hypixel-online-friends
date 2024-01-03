"""Contains functions for dealing with reading from the results folder."""

import os
import os.path
from typing import Optional, List, Dict
from copy import deepcopy
import copy

import Utils
import Files
from MyClasses import UUID_Plus_Time
import hypixel
from Args import Args

_all_dicts_standard_files: Optional[List[dict]] = None
_all_dicts_additional_friends_files: Optional[List[dict]] = None
_all_dicts_unique_uuids: Optional[List[dict]] = None
_ign_uuid_pairs_in_results: Optional[Dict[str, str]] = None
_uuid_ign_pairs_in_results: Optional[Dict[str, str]] = None
_player_uuids_with_f_list_in_results: Optional[List[str]] = None

_NON_TRIVIAL_KEYS = ['friends', 'name', 'fkdr', 'star', 'pit_rank']
_get_only_non_trivial_dicts: Optional[bool] = None

_args: Optional[Args] = None

def ign_uuid_pairs_in_results(get_deepcopy: bool = False) -> Dict[str, str]:
    global _ign_uuid_pairs_in_results

    if not _ign_uuid_pairs_in_results:
        _ign_uuid_pairs_in_results = {}
        for d in (get_all_dicts_in_results(True, False, True) + get_all_dicts_in_results(True, False, False)):
            _ign_uuid_pairs_in_results.update(Utils.get_all_ign_uuid_pairs_in_dict(d))
    return deepcopy(_ign_uuid_pairs_in_results) if get_deepcopy else _ign_uuid_pairs_in_results

def uuid_ign_pairs_in_results(get_deepcopy: bool = False) -> Dict[str, str]:
    global _uuid_ign_pairs_in_results

    if not _uuid_ign_pairs_in_results:
        _uuid_ign_pairs_in_results = {}
        for d in (get_all_dicts_in_results(True, False, True) + get_all_dicts_in_results(True, False, False)):
            _uuid_ign_pairs_in_results.update(Utils.get_all_ign_uuid_pairs_in_dict(d, False, True))
    return deepcopy(_uuid_ign_pairs_in_results) if get_deepcopy else _uuid_ign_pairs_in_results

def check_results(only_non_trivial_dicts: bool, uuid: Optional[str], ign: Optional[str]) -> None:
    """Traverses through the results folder and prints some stats and info. If a uuid and ign are provided,
       then some specific info about that player will be outputted as well."""
    global _player_uuids_with_f_list_in_results

    _consistency_check_trivial_dicts_policy(only_non_trivial_dicts)
    assert type(uuid) == type(ign)

    if not only_non_trivial_dicts:
        print(str(len(get_all_dicts_unique_uuids_in_results(False))) + 
              " total unique uuids recorded in the results folder.")
        return

    all_dicts: List[dict] = get_all_dicts_unique_uuids_in_results(True)
    print(str(len(all_dicts)) + " total players with non-trivial data stored in the results folder.")

    for k in _NON_TRIVIAL_KEYS:
        dicts_with_key = [d for d in all_dicts if k in d]
        indent = "  "
        Utils.print_info_for_key(dicts_with_key, k, indent)
        if k != 'friends':
            continue
        _player_uuids_with_f_list_in_results = [d['uuid'] for d in dicts_with_key]
        if uuid:
            print(indent*2 + "Also, it's " + 
                  Utils.bool_lowercase_str(uuid in _player_uuids_with_f_list_in_results) +
                  " that " + ign + "'s friends list is in the results folder.")
    print('\n\n')

def player_uuids_with_f_list_in_results(get_copy: bool = False) -> List[str]:
    global _player_uuids_with_f_list_in_results

    if not _player_uuids_with_f_list_in_results:
        raise ValueError("Probably haven't called the checkresults() function yet.")
    return (copy.copy(_player_uuids_with_f_list_in_results) if get_copy
            else _player_uuids_with_f_list_in_results)

def get_all_dicts_in_results(only_non_trivial_dicts: bool, get_deepcopy: bool = False,
                             get_additional_friends: bool = False) -> List[dict]:
    """Returns a flat list of dicts, for all dicts/nested dicts found in the results folder. 
       Note that there can be multiple dicts with the same uuid."""
    global _all_dicts_standard_files
    global _all_dicts_additional_friends_files
    
    _consistency_check_trivial_dicts_policy(only_non_trivial_dicts)
    all_dicts = _all_dicts_additional_friends_files if get_additional_friends else _all_dicts_standard_files

    if not all_dicts:
        all_dicts = []
        for d in _get_all_jsons_in_results(get_additional_friends=get_additional_friends):
            all_dicts.extend(Utils.get_all_nested_dicts_in_dict(d, make_deepcopy=False))
        if only_non_trivial_dicts:
            all_dicts = _get_only_non_trivial_keys_in_dict(all_dicts)
        # Now save the result so that potential future calls won't have to recompute:
        if get_additional_friends:
            _all_dicts_additional_friends_files = all_dicts
        else:
            _all_dicts_standard_files = all_dicts

    return deepcopy(all_dicts) if get_deepcopy else all_dicts

def get_all_dicts_unique_uuids_in_results(only_non_trivial_dicts: bool, get_deepcopy: bool = False,
                                          must_have_times_friended: bool = False) -> List[dict]:
    """Returns a flat list of dicts (no more than one per uuid), for all dicts/nested dicts found in the 
    results folder (excluding additional friends files). If multiple dicts have the same uuid, the one with 
    the biggest friends list will be kept."""
    global _all_dicts_unique_uuids

    _consistency_check_trivial_dicts_policy(only_non_trivial_dicts)

    if not _all_dicts_unique_uuids:
        _all_dicts_unique_uuids = Utils.remove_dicts_duplicate_uuids(
            get_all_dicts_in_results(only_non_trivial_dicts),
            must_have_times_friended=must_have_times_friended
        )

    return deepcopy(_all_dicts_unique_uuids) if get_deepcopy else _all_dicts_unique_uuids

def get_best_f_list_for_player_in_results(uuid_or_ign: str,
                                          must_have_times_friended: bool = False) -> List[UUID_Plus_Time]:
    uuid = hypixel.get_uuid(uuid_or_ign)
    for d in get_all_dicts_unique_uuids_in_results(True, must_have_times_friended=must_have_times_friended):
        if d['uuid'] == uuid:
            # print(d['filename']) For debugging - will show you the filename the dict came from.
            return [UUID_Plus_Time(f['uuid'], f.get('time', None)) for f in d.get('friends', [])]
    return []

def update_list_if_applicable(lst: List[UUID_Plus_Time], new_elem: UUID_Plus_Time) -> None:
    """If no element in lst refers to the same person as elem, then elem will be appended at the end.
       Otherwise, elem will replace its duplicate, if it is more recent than it.
       The reference to the list itself will be modified by this function."""
    for i, element in enumerate(lst):
        if new_elem.refers_to_same_person(element):
            if new_elem.more_recent(element):
                lst[i] = new_elem
            return
    lst.append(new_elem)

def get_all_additional_friends_for_player(uuid_or_ign: str) -> List[UUID_Plus_Time]:
    uuid = hypixel.get_uuid(uuid_or_ign)
    additional_friends: List[UUID_Plus_Time] = []
    for d in get_all_dicts_in_results(True, get_additional_friends=True):
        if d['uuid'] != uuid:
            continue
        for f in d.get('friends', []):
            current_friend = UUID_Plus_Time(f['uuid'], f.get('time', None))
            update_list_if_applicable(additional_friends, current_friend)
    return additional_friends

def print_all_matching_uuids_or_igns(uuid_or_ign: str) -> None:
    """This function will traverse results, and find all igns or uuids that are grouped with
       the uuid_or_ign param. For most igns/uuids, there will only be one result printed, but
       some players may change their ign, and others could take over the ign."""

    param_key = 'uuid' if Utils.is_uuid(uuid_or_ign) else 'name'
    search_for = 'name' if param_key == 'uuid' else 'uuid'

    print('\nMatching ' + search_for + 's found in the results folder:')
    hits = []
    for d in get_all_dicts_in_results(True):
        if 'name' in d and d[param_key].lower() == uuid_or_ign.lower() and d[search_for] not in hits:
            print(d[search_for])
            hits.append(d[search_for])
    print()

def _get_all_jsons_in_results(get_additional_friends: bool = False) -> List[dict]:
    """Returns a list of dicts, where each dict represents the json each textfile stores."""
    all_jsons: List[dict] = []
    all_files = os.listdir('results')
    all_files = [f for f in all_files if _does_filename_meet_reqs(f, get_additional_friends)]
    assert _args
    for f in all_files:
        filename = os.path.join('results', f)
        is_multi_player_file = any(x in f for x in [' plus ', ' minus ', ' intersect '])
        if is_multi_player_file and not _args.include_multi_player_files():
            continue
        json_in_file = Files.read_json_textfile(filename)
        json_in_file['filename'] = filename
        if is_multi_player_file and _args.skip_first_dict_in_multi_player_files():
            json_in_file['exclude'] = '' # Adding this key as a signal to exclude this 
                                         # outermost dict of the file, when unnesting.
        all_jsons.append(json_in_file)
    return all_jsons

def _does_filename_meet_reqs(f: str, for_additional_friends: bool = False) -> bool:
    if for_additional_friends:
        return f.startswith('Additional friends of') and f.endswith('.txt')
    return f.startswith('Friends of') and f.endswith('.txt')

def _get_only_non_trivial_keys_in_dict(dicts: List[dict]) -> List[dict]:
    return [d for d in dicts if any(k in d for k in _NON_TRIVIAL_KEYS)]

def _consistency_check_trivial_dicts_policy(get_non_trivial_dicts_param: bool) -> None:
    global _get_only_non_trivial_dicts

    if _get_only_non_trivial_dicts is None:
        _get_only_non_trivial_dicts = get_non_trivial_dicts_param
    elif _get_only_non_trivial_dicts != get_non_trivial_dicts_param:
        # Once set, the global should never be contradicted.
        raise ValueError('Already specified to either include/exclude trivial dicts.')
    
def set_args(args: Args) -> None:
    global _args
    assert not _args
    _args = deepcopy(args)