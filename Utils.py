"""Functions in this file are the most general, and don't have dependencies on other files in the project."""

from datetime import datetime
import time
from typing import List, Optional, Union, Iterable, Any, Type
from collections import OrderedDict
from copy import deepcopy
import math
from pprint import pprint

def list_subtract(main_list: List, subtract_elems: Iterable) -> List:
    subtract_set = set(subtract_elems)
    return [x for x in main_list if x not in subtract_set]

def remove_duplicates(lst: List) -> List:
    return list(OrderedDict.fromkeys(deepcopy(lst))) # regular dict works to maintain order for python >= 3.7

def is_date_string(text: str) -> bool:
    try:
        datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        return False
    return True

def print_list(lst: List, prepended_msg: str = "", separator: str = " ", appended_msg: str = "\n\n") -> None:
    print(prepended_msg, end="")
    print(separator.join([str(x) for x in lst]), end=appended_msg)

def trim_if_needed(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    side_lengths = int((limit - 5) / 2)
    return text[:side_lengths].strip() + ' ..... ' + text[-side_lengths:].strip()

def remove_date_strings(lst: List[str]) -> List[str]:
    return [x for x in lst if not is_date_string(x)]

def get_date_string_if_exists(lst: List[str]) -> Optional[str]:
    """If no date strings found, return None."""
    return next((x for x in lst if is_date_string(x)), None)

def kdr_division(kills: int, deaths: int) -> float:
    return kills / deaths if deaths else float(kills)

def date_to_epoch(date_string: str, in_seconds: bool) -> float:
    epoch = time.mktime(datetime.strptime(date_string, '%Y-%m-%d').timetuple())
    return epoch * 1000 if not in_seconds else epoch

def epoch_to_date(epoch: float, in_seconds: bool) -> str:
    return datetime.fromtimestamp(epoch / 1000 if not in_seconds else epoch).strftime('%Y-%m-%d')

def find_dict_for_given_player(d: dict, uuid_or_ign: str, make_deep_copy: bool = True,
                               dict_must_have_friends_list: bool = True) -> Optional[dict]:
    """ d will be a dictionary read from a file in json format - it will have a uuid key, and possibly
    a name, fkdr, and friends key. The friends key would have a value that is a list of dictionaries,
    recursively following the same dictionary requirements."""
    if make_deep_copy:
        d = deepcopy(d)
    if ((is_uuid(uuid_or_ign) and d['uuid'] == uuid_or_ign) or
        (is_ign(uuid_or_ign) and 'name' in d and d['name'].lower() == uuid_or_ign.lower())):
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

    assert len(uuid_or_ign) in (32, 36) or len(uuid_or_ign) <= 16
    return len(uuid_or_ign) in (32, 36)

def is_ign(uuid_or_ign: str) -> bool:
    """This function returns whether 'uuid_or_ign' is an ign.
       Precondition: uuid_or_ign must be either a uuid or ign."""
    return not is_uuid(uuid_or_ign)

def get_all_ign_uuid_pairs_in_dict(d: dict, make_deepcopy: bool = False,
                                   get_uuid_ign_pairs_instead: bool = False) -> dict:
    """Traverses the d param and returns a dict, where each key-value pair represents an ign-uuid
    pair found in d (unless `get_uuid_ign_pairs_instead` is True, in which case uuid-ign pairs are built)."""
    if make_deepcopy:
        d = deepcopy(d)
    ign_uuid_pairs = {}
    if 'name' in d:
        name_lower = d['name'].lower()
        if get_uuid_ign_pairs_instead:
            ign_uuid_pairs[d['uuid']] = name_lower
        else:
            ign_uuid_pairs[name_lower] = d['uuid']
    for friend_dict in d.get('friends', []):
        ign_uuid_pairs.update(get_all_ign_uuid_pairs_in_dict(friend_dict, False, get_uuid_ign_pairs_instead))
    return ign_uuid_pairs

def get_all_nested_dicts_in_dict(d: dict, make_deepcopy: bool = False) -> List[dict]:
    """Traverses through d and returns a list of d and all its nested friend dicts."""
    if make_deepcopy:
        d = deepcopy(d)
    dicts = [d] if 'exclude' not in d else []
    for friend_dict in d.get('friends', []):
        friend_dict['filename'] = d['filename']
        dicts.extend(get_all_nested_dicts_in_dict(friend_dict, make_deepcopy=False))
    return dicts

def print_info_for_key(dicts: List[dict], k: str, indent: str) -> None:
    k_for_print = k + ('s' if k == 'star' else '')
    print(f"{indent}{len(dicts)} players with their {k_for_print} recorded in results.")
    if k in ('star', 'fkdr', 'friends'):
        highest_dict = max(dicts, key=lambda d: len(d[k]) if k == 'friends' else d[k])
        highest_stat = len(highest_dict[k]) if k == 'friends' else highest_dict[k]
        name = f"{highest_dict['name']}, " if 'name' in highest_dict else ''
        print(f"{indent*2}Most {k_for_print}: {highest_stat} ({name}uuid {highest_dict['uuid']})")

def does_first_have_more_friends(first: list, second: list) -> Optional[bool]:
    """True returned if more, False returned if less, None returned if equal."""
    return True if len(first) > len(second) else (False if len(second) > len(first) else None)

def does_first_record_times_better(first: list, second: list) -> Optional[bool]:
    """True returned if better, False returned if worse, None returned if equal."""
    first_has_times = len(first) > 0 and 'time' in first[0]
    second_has_times = len(second) > 0 and 'time' in second[0]
    return None if (first_has_times == second_has_times) else first_has_times

def does_first_have_more_keys(first: dict, second: dict) -> Optional[bool]:
    """True returned if more, False returned if less, None returned if equal."""
    return None if len(first.keys()) == len(second.keys()) else len(first.keys()) > len(second.keys())

def is_first_dict_more_valuable(first: dict, second: dict, must_have_times_friended: bool) -> bool:
    """Returns true if the second dict should be replaced with the first dict, based off
       some criteria. This function is called by the 'remove_dicts_duplicate_uuids' function."""
    assert first['uuid'] == second['uuid']
    first_friends, second_friends = first.get('friends', []), second.get('friends', [])

    comparisons: List[Optional[bool]] = [
        does_first_have_more_friends(first_friends, second_friends),
        does_first_record_times_better(first_friends, second_friends),
        does_first_have_more_keys(first, second)
    ]
    if must_have_times_friended:
        comparisons[0], comparisons[1] = comparisons[1], comparisons[0]

    return next((b for b in comparisons if b is not None), False)

def remove_dicts_duplicate_uuids(dicts: List[dict], make_deepcopy: bool = False,
                                 must_have_times_friended: bool = False) -> List[dict]:
    """ For dicts with the same uuid, only one dict will be kept in the new list. The criteria
        for choosing which one are as follows (in order):
        - bigger friends list
        - records time added for friends
        - more keys in dict
        - The dict that came first in the `dicts` param
        Note that 1) and 2) are swapped, if the `must_have_times_friended` param is set to True. """
    if make_deepcopy:
        dicts = deepcopy(dicts)
    dicts_unique_uuids: dict = {} # Key uuid, value a dict (one of the elements in dicts).
    for d in dicts:
        uuid = d['uuid']
        if (uuid not in dicts_unique_uuids or is_first_dict_more_valuable(d, dicts_unique_uuids[uuid],
        must_have_times_friended)):
            dicts_unique_uuids[uuid] = d
    return list(dicts_unique_uuids.values())

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

def replace_in_list(lst: List[str], elem_to_remove: str, list_to_insert: List[str]) -> List[str]:
    """Returns a new list, where any occurrences of `elem_to_remove` (case-insensitive) in `lst` are
       replaced with the elements in `list_to_insert`. `lst` will not be modified."""
    replacement: List[str] = []
    for s in lst:
        if s.lower() == elem_to_remove.lower():
            replacement.extend(list_to_insert)
        else:
            replacement.append(s)
    return replacement

def contains_whitespace(s: str) -> bool:
    return s != remove_whitespace(s)

def remove_whitespace(s: str) -> str:
    return ''.join(s.split())

def num_to_roman(num: int) -> str:
    if num == 0:
        return "0"
    # https://stackoverflow.com/a/40274588/7743427:
    num_map = ((1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
               (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I'))
    roman = ''
    while num > 0:
        for i, r in num_map:
            while num >= i:
                roman += r
                num -= i
    return roman

def roman_to_num(roman: str) -> int:
    # https://stackoverflow.com/a/52426119/7743427:
    d = {'m': 1000, 'd': 500, 'c': 100, 'l': 50, 'x': 10, 'v': 5, 'i': 1}
    n = [d[i] for i in roman.lower() if i in d]
    return sum(i if i>=n[min(j+1, len(n)-1)] else -i for j,i in enumerate(n))

def get_prestige_from_pit_rank(pit_rank: str) -> int:
    """pit_rank should be of the form: *roman number/decimal number* *-* *decimal number from 1 to 120*
    Will return an int representing the prestige number."""
    prestige_str = pit_rank.split('-')[0]
    prestige = int(prestige_str) if prestige_str.isdigit() else roman_to_num(prestige_str)
    assert 0 <= prestige <= 50
    return prestige

def get_level_from_pit_rank(pit_rank: str) -> int:
    """pit_rank should be of the form: *roman number/decimal number* *-* *decimal number from 1 to 120*
    Will return an int representing the level number."""
    level = int(pit_rank.split('-')[1])
    assert 1 <= level <= 120
    return level

def pit_rank_to_num_for_sort(pit_rank: str) -> int:
    """pit_rank should be of the form: *roman number/decimal number* *-* *decimal number from 1 to 120*
    Will return an int equal to the prestige number * 120 + level number"""
    return get_prestige_from_pit_rank(pit_rank) * 120 + get_level_from_pit_rank(pit_rank)

def round_up_to_closest_multiple(num: float, multiple_of: int) -> int:
    """E.g., calling with args (101, 50) would return 150."""
    return math.ceil(num / multiple_of) * multiple_of

def percentify(d: float, decimal_places_to_round_to: int = 2) -> str:
    return f"{round(100*d, decimal_places_to_round_to)}%"

def normalize_against_max_val(l: Iterable[float]) -> List[float]:
    max_val = max(l)
    return [i / max_val for i in l]

def nested_get(d: dict, nested_keys: Iterable, default_val: Any, expected_type: Optional[Type] = None) -> Any:
    try:
        for k in nested_keys:
            d = d[k]
        return_val = d
    except KeyError:
        return_val = default_val
    assert expected_type is None or type(return_val) == expected_type
    return return_val

def print_diff_dicts(old_dict: dict, new_dict: dict, prepended_msg: str = '') -> None:
    from deepdiff import DeepDiff # type: ignore
    print(prepended_msg, end='')
    pprint(DeepDiff(old_dict, new_dict), indent=2)