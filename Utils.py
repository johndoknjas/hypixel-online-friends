"""Functions in this file are the most general, and don't have dependencies on other files in the project."""

import datetime
import time
from typing import List, Optional
from collections import OrderedDict
from copy import deepcopy

def list_subtract(main_list: List, subtract_list: List) -> List:
    return [x for x in main_list if x not in subtract_list]

def remove_duplicates(lst: List) -> List:
    return deepcopy(list(OrderedDict.fromkeys(lst))) # regular dict works to maintain order for python >= 3.7

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
    return (text[:limit] + '.....') if len(text) > limit else text

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

# https://stackoverflow.com/questions/49566650/deepcopy-all-function-arguments/49566747#49566747
def deep_copy_params(to_call):
    def f(*args, **kwargs):
        return to_call(*deepcopy(args), **deepcopy(kwargs))
    return f