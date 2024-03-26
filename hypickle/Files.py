"""Contains functions related to working with files. Only dependencies should be stuff in Utils.py,
and stuff in this same file."""

import os
import os.path
import json
import time
from typing import Optional, Dict, List, Iterable, Tuple
from copy import deepcopy
import shutil
import ntpath
from string import whitespace

from . import Utils

_ALIASES_FILENAME = "aliases.txt"
_UUIDS_FILENAME = "uuids.txt"

_ign_uuid_pairs: Optional[dict] = None

def write_data_as_json_to_file(data: dict, description: str, folder_name: str = "results") -> None:
    warning_msg = """About to output a player's friends list to a file. Note that for any additional
                     friends not currently in such a 'standard list', their displayed old name in
                     parentheses going forward will be their ign as of today.
                     To proceed, press y: """
    warning_msg = ' '.join(warning_msg.split()) + ' '
    if description.lower().startswith('friends of') and input(warning_msg).lower() != 'y':
        return
    filename = create_file(description, folder_name)
    with open(filename, "w") as f:
        f.write(json.dumps(data, indent=4))

def create_file(description: str, folder_name: str) -> str:
    """Creates a file using the params and returns the name of the file, which can be used by the caller if desired."""
    filename = os.path.join(folder_name, Utils.trim_if_needed(f"{description} - {time.time_ns()}.txt"))
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    return filename

def ign_uuid_pairs_in_uuids_txt(do_deepcopy: bool = False) -> dict:
    """Retrieves pairs stored in the uuids.txt file as a dict - key ign, value uuid"""
    global _ign_uuid_pairs
    if _ign_uuid_pairs is not None:
        return deepcopy(_ign_uuid_pairs) if do_deepcopy else _ign_uuid_pairs
    _ign_uuid_pairs = {} # key ign, value uuid
    if not os.path.isfile(_UUIDS_FILENAME):
        return {}
    with open(_UUIDS_FILENAME) as file:
        for line in file:
            words = line.rstrip().split()
            _ign_uuid_pairs[words[0].lower()] = words[1]
    return deepcopy(_ign_uuid_pairs) if do_deepcopy else _ign_uuid_pairs

def read_json_textfile(filepath: str) -> dict:
    try:
        with open(filepath, 'r') as f:
            return json.loads(f.read())
    except FileNotFoundError:
        # This could happen if the user gives a windows path when running the program with wsl. So try this:
        with open('results/' + ntpath.basename(filepath), 'r') as f:
            return json.loads(f.read())

def update_uuids_file(ign_uuid_pairs: Dict[str, str]) -> None:
    """Updates the uuids.txt file with the ign_uuid_pairs param.
    If a uuid is found for an ign in uuids.txt that conflicts with a pair in the passed in param,
    it will be replaced. Also, this function will make a backup of uuids.txt before overwriting it."""

    if os.path.isfile(_UUIDS_FILENAME):
        shutil.copy(_UUIDS_FILENAME, create_file('uuids copy', 'old-uuids'))
    pairs = ign_uuid_pairs_in_uuids_txt(do_deepcopy=True)
    pairs.update(ign_uuid_pairs)
    with open(_UUIDS_FILENAME, "w") as file:
        for key, value in pairs.items():
            file.write(f"{key} {value}\n")
            assert key == key.lower()
    print(f"{_UUIDS_FILENAME} now contains uuid-ign pairs for {len(pairs)} players.")

def assertions_for_aliases(alias: str, meaning: str, keywords: Iterable[str]) -> None:
    assert alias not in keywords and not Utils.contains_whitespace(alias)
    assert '.txt' not in meaning and '.txt' not in alias

def get_new_aliases_from_user(aliases: Dict[str, str], keywords: Iterable[str]) -> None:
    """Asks the user for new aliases, and updates the `aliases` parameter accordingly."""
    while True:
        alias = input("Enter alias (or 'done'/'stop' to quit): ").lower()
        if alias in ('done', 'stop', 'quit'):
            return
        meaning = input("Enter the text this alias stands for: ").lower()
        if meaning in ('del', 'delete', 'remove'):
            if input(f"Confirm you want to delete the {alias} alias by entering y: ") in ('y', 'Y'):
                del aliases[alias]
            continue
        elif meaning == 'append':
            new_words = input(f"Enter the new word(s) to append to this alias' meaning: ").lower().split()
            meaning = ' '.join(aliases[alias].split() + new_words)
        elif meaning in ('shorten', 'trim'):
            remove_words = input(f"Enter the word(s) to remove from this alias' meaning: ").lower().split()
            meaning = ' '.join(x for x in aliases[alias].split() if x not in remove_words)
        if alias in aliases:
            print(f"'{alias}' is already an alias that stands for '{aliases[alias]}'. ", end='')
            if input(f"To confirm replacing its meaning to be '{meaning}', enter y: ") not in ('y', 'Y'):
                continue
        assertions_for_aliases(alias, meaning, keywords)
        aliases[alias] = meaning
        print()

def add_new_ign_uuid_aliases(
        aliases: Dict[str, str], ign_uuid_pairs: Iterable[Tuple[str, str]], keywords: Iterable[str]
    ) -> None:
    """Makes each ign an alias for its uuid, and adds it to `aliases` (if the ign is not
       already an existing alias)."""
    for ign, uuid in ((a.lower(), b.lower()) for a, b in ign_uuid_pairs):
        assert Utils.is_ign(ign) and Utils.is_uuid(uuid)
        assertions_for_aliases(ign, uuid, keywords)
        if ign in aliases:
            print(f"The alias {ign} already exists, so not replacing it.")
        else:
            aliases[ign] = uuid

def update_aliases(
        keywords: Iterable[str], ign_uuid_pairs: Optional[Iterable[Tuple[str, str]]] = None
    ) -> None:
    """ Updates aliases using user input if `ign_uuid_pairs` is None. Otherwise, goes through each
        2-tuple in `ign_uuid_pairs` and makes the ign (first elem) an alias for the uuid (second elem). """
    print_aliases()
    aliases: Dict[str, str] = get_aliases_with_str_meanings()
    aliases_copy = deepcopy(aliases)
    if ign_uuid_pairs is None:
        get_new_aliases_from_user(aliases, keywords)
    else:
        add_new_ign_uuid_aliases(aliases, ign_uuid_pairs, keywords)

    if os.path.isfile(_ALIASES_FILENAME):
        shutil.copy(_ALIASES_FILENAME, create_file('aliases copy', 'old-aliases'))
    with open(_ALIASES_FILENAME, 'w') as file:
        for a,m in sorted(aliases.items()):
            file.write(f'"{a}" = "{m}"\n')

    print_aliases(starting_phrase="\nNow")
    assert aliases == get_aliases_with_str_meanings()
    old_items, new_items = set(aliases_copy.items()), set(aliases.items())
    print(f"\nNew aliases - old aliases: {new_items - old_items}")
    print(f"Old aliases - new aliases: {old_items - new_items}")

def get_aliases_with_str_meanings() -> Dict[str, str]:
    """Does the same thing as `get_aliases()`, but each of the meanings is a string with words
       separated by spaces, rather than a list."""
    return {a: ' '.join(m) for a,m in get_aliases().items()}

def get_aliases() -> Dict[str, List[str]]:
    """ Returns a list representing the aliases stored in aliases.txt. Each element of this list
        will be a tuple, where the first element is a string (the alias), and the second element
        is a list of strings (what the alias stands for). """
    if not os.path.isfile(_ALIASES_FILENAME):
        return {}
    with open(_ALIASES_FILENAME, 'r') as file:
        lines: List[str] = file.read().splitlines()
    aliases: Dict[str, List[str]] = {}
    for line in lines:
        split_line = [x.strip(whitespace + '"') for x in line.split('=')]
        assert line.count('=') == 1 and len(split_line) == 2 and line == line.lower()
        aliases[split_line[0]] = split_line[1].split()
    return aliases

def print_aliases(starting_phrase: str = 'Currently') -> None:
    aliases = get_aliases()
    print(f"{starting_phrase} {len(aliases)} aliases:\n")
    for alias in aliases:
        print(f"{alias} = {aliases[alias]}")
    print()

def apply_aliases(lst: List[str]) -> List[str]:
    """Returns a new list that results from applying the aliases (in aliases.txt) to the strings in lst."""
    old_lst = lst
    for alias in (aliases := get_aliases()):
        lst = Utils.replace_in_list(lst, alias, aliases[alias])
    # If lst got updated, keep recursing (as some aliases may have aliases of their own):
    return apply_aliases(lst) if lst != old_lst else lst
