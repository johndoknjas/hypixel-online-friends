"""Functions in this file are the most general, and don't have dependencies on other files in the project."""

from datetime import datetime
import time
from typing import List, Optional, TypeVar, Callable, Any, Union
from collections import OrderedDict
from copy import deepcopy
import operator

T = TypeVar('T')

def list_subtract(main_list: List, subtract_list: List) -> List:
    return [x for x in main_list if x not in subtract_list]

def remove_duplicates(lst: List) -> List:
    return list(OrderedDict.fromkeys(deepcopy(lst))) # regular dict works to maintain order for python >= 3.7

def is_date_string(text: str) -> bool:
    try:
        datetime.strptime(text, '%Y-%m-%d')
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
    epoch = time.mktime(datetime.strptime(date_string, '%Y-%m-%d').timetuple())
    if not in_seconds:
        epoch *= 1000
    return epoch

def epoch_to_date(epoch: float, in_seconds: bool) -> str:
    if not in_seconds:
        epoch /= 1000
    return datetime.utcfromtimestamp(epoch).strftime('%Y-%m-%d')

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

def get_all_ign_uuid_pairs_in_dict(d: dict, make_deepcopy: bool = False) -> dict:
    """Traverses the d param and returns a dict, where each key-value pair represents an ign-uuid 
    pair found in d."""
    if make_deepcopy:
        d = deepcopy(d)
    uuid_name_pairs = {}
    if 'name' in d:
        uuid_name_pairs[d['name'].lower()] = d['uuid']
    for friend_dict in d.get('friends', []):
        uuid_name_pairs.update(get_all_ign_uuid_pairs_in_dict(friend_dict, make_deepcopy=False))
    return uuid_name_pairs

def get_all_nested_dicts_in_dict(d: dict, make_deepcopy: bool = False) -> List[dict]:
    """Traverses through d and returns a list of d and all its nested friend dicts."""
    if make_deepcopy:
        d = deepcopy(d)
    dicts = [d]
    for friend_dict in d.get('friends', []):
        dicts.extend(get_all_nested_dicts_in_dict(friend_dict, make_deepcopy=False))
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

def remove_dicts_duplicate_uuids(dicts: List[dict], make_deepcopy: bool = False) -> List[dict]:
    """ For dicts with the same uuid, only one dict will be kept in the new list. The criteria
        for choosing which one is which dict has the bigger friends list. If neither has a friends list,
        the one that comes earlier in the 'dicts' param will be kept. """
    if make_deepcopy:
        dicts = deepcopy(dicts)
    dicts_unique_uuids: dict = {} # Key uuid, value a dict (one of the elements in dicts).
    for d in dicts:
        uuid = d['uuid']
        if (uuid not in dicts_unique_uuids or
            len(d.get('friends', [])) > len(dicts_unique_uuids[uuid].get('friends', []))):
            dicts_unique_uuids[uuid] = d
    return list(dicts_unique_uuids.values())

def cmp_element_val(l: list[T], index: int, val: T, cmp_func: Callable[[Any, Any], bool] = operator.eq) -> bool:
    """Returns true if index is in-bounds, and if a comparison between the associated element and 'val' is True.
    By default this comparison is just operator.eq (i.e., ==), but a function can be passed for cmp_func
    to specify a function to use.
    This is probably overengineered just to abstract away index checking, but it's fun."""
    return index < len(l) and cmp_func(l[index], val)

def is_in_milliseconds(epoch_val: Union[float, int]) -> bool:
    """epoch_val is assumed to be in either seconds or milliseconds"""
    return epoch_val > 10000000000

def convert_to_seconds(time_val: Union[float, int, str, None]) -> float:
    """ Converts a datestring or epoch to epoch in seconds. If time_val is already an epoch, it must be
        in seconds or milliseconds form. """
    if time_val is None:
        return 0
    elif isinstance(time_val, str):
        assert is_date_string(time_val)
        return date_to_epoch(time_val, True)
    elif is_in_milliseconds(time_val):
        return time_val / 1000
    else:
        return time_val

def is_older(time_one: Union[str, float, int, None], time_two: Union[str, float, int, None]) -> bool:
    """Returns true if time_one is more recent than time_two. time_one and time_two must each be either
       a datestring or epoch (in seconds/milliseconds)."""
    return convert_to_seconds(time_one) < convert_to_seconds(time_two)

def get_current_date() -> str:
    return datetime.now().strftime('%Y-%m-%d')
