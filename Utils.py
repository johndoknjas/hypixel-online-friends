"""Functions in this file are the most general, and don't have dependencies on other files in the project."""

import datetime
import time
from typing import List, Optional
from collections import OrderedDict
from copy import deepcopy

def list_subtract(main_list: List, subtract_list: List) -> List:
    return [x for x in main_list if x not in subtract_list]

def remove_duplicates(lst: List) -> List:
    return list(OrderedDict.fromkeys(deepcopy(lst))) # regular dict works to maintain order for python >= 3.7

def is_date_string(text: str) -> bool:
    try:
        datetime.datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        return False
    else:
        return True

def print_list_of_dicts(lst: List[dict]) -> None:
    print("\n".join([str(d) for d in lst]))

def trim_if_needed(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    side_lengths = int((limit - 5) / 2)
    return text[:side_lengths].strip() + ' ..... ' + text[-side_lengths:].strip()

def remove_date_strings(lst: List[str]) -> List[str]:
    return [x for x in deepcopy(lst) if not is_date_string(x)]

def get_date_string_if_exists(lst: List[str]) -> Optional[str]:
    """If no date strings found, return None."""
    return next((x for x in deepcopy(lst) if is_date_string(x)), None)

def fkdr_division(final_kills: int, final_deaths: int) -> float:
    return final_kills / final_deaths if final_deaths else float(final_kills)

def date_to_epoch(date_string: str, in_seconds: bool) -> float:
    epoch = time.mktime(datetime.datetime.strptime(date_string, '%Y-%m-%d').timetuple())
    if not in_seconds:
        epoch *= 1000
    return epoch

def epoch_to_date(epoch: float, in_seconds: bool) -> str:
    if not in_seconds:
        epoch /= 1000
    return datetime.datetime.utcfromtimestamp(epoch).strftime('%Y-%m-%d')

def find_path_to_key_in_nested_dict(data, target_key):
    """Can use this function to find the path to some key in a nested dict."""
    def search(obj, path):
        if isinstance(obj, dict):
            if target_key in obj:
                return f"{path}[{target_key}]"
            for key, value in obj.items():
                if (inner_path := search(value, f"{path}[{key}]")) is not None:
                    return inner_path
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if (inner_path := search(item, f"{path}[{i}]")) is not None:
                    return inner_path
        return None
    return search(data, "dict")

def find_value_of_nested_key(data, key):
    if isinstance(data, dict):
        if key in data:
            return data[key]
        else:
            for value in data.values():
                if (result := find_value_of_nested_key(value, key)) is not None:
                    return result
    elif isinstance(data, list):
        for element in data:
            if (result := find_value_of_nested_key(element, key)) is not None:
                return result
    return None

def find_dict_for_given_player(d: dict, uuid_or_ign: str, make_deep_copy: bool = True,
                               dict_must_have_friends_list: bool = True) -> Optional[dict]:
    """ d will be a dictionary read from a file in json format - it will have a uuid key, and possibly
    a name, fkdr, and friends key. The friends key would have a value that is a list of dictionaries,
    recursively following the same dictionary requirements."""
    if make_deep_copy:
        d = deepcopy(d)
    if ((is_uuid(uuid_or_ign) and d['uuid'] == uuid_or_ign) or
        (not is_uuid(uuid_or_ign) and 'name' in d and d['name'].lower() == uuid_or_ign.lower())):
        if 'friends' in d or not dict_must_have_friends_list:
            return d
    for friend_dict in d.get('friends', []):
        if result := find_dict_for_given_player(friend_dict, uuid_or_ign, make_deep_copy=False,
                                                dict_must_have_friends_list=dict_must_have_friends_list):
            return result
    return None

def is_uuid(uuid_or_ign: str) -> bool:
    """This function returns whether 'uuid_or_ign' is a uuid.
    Precondition: uuid_or_ign must be either a uuid or ign."""
    if len(uuid_or_ign) in (32, 36):
        return True
    elif len(uuid_or_ign) <= 16:
        return False
    else:
        raise ValueError("Invalid length")

def get_all_ign_uuid_pairs_in_dict(d: dict, make_deepcopy: bool = True) -> dict:
    """Traverses the d param and returns a dict, where each key-value pair represents an ign-uuid 
    pair found in d."""
    if make_deepcopy:
        d = deepcopy(d)
    uuid_name_pairs = {}
    if 'name' in d:
        uuid_name_pairs[d['name'].lower()] = d['uuid']
    for friend_dict in d.get('friends', []):
        uuid_name_pairs.update(get_all_ign_uuid_pairs_in_dict(friend_dict, False))
    return uuid_name_pairs

def get_all_nested_dicts_in_dict(d: dict, make_deepcopy: bool = True) -> List[dict]:
    """Traverses through d and returns a list of d and all its nested friend dicts."""
    if make_deepcopy:
        d = deepcopy(d)
    dicts = [d]
    for friend_dict in d.get('friends', []):
        dicts.extend(get_all_nested_dicts_in_dict(friend_dict, False))
    return dicts

def bool_lowercase_str(b: bool) -> str:
    return str(b).lower()

def print_info_for_key(dicts: List[dict], k: str, indent: str) -> None:
    k_for_print = k + ('s' if k == 'star' else '')
    print(indent + str(len(dicts)) + " players with their " + k_for_print + " recorded in results.")
    if k in ('star', 'fkdr', 'friends'):
        highest_dict = max(dicts, key=lambda d: len(d[k]) if k == 'friends' else d[k])
        print(indent*2 + "Most " + k_for_print + ": " + 
                str(len(highest_dict[k]) if k == 'friends' else highest_dict[k]) + 
                " (" + ((highest_dict['name'] + ", ") if 'name' in highest_dict else "") + 
                'uuid ' + highest_dict['uuid'] + ")")