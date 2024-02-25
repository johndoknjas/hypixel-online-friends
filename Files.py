"""Contains functions related to working with files. Only dependencies should be stuff in Utils.py,
and stuff in this same file."""

import os
import os.path
import json
import time
from typing import Optional, Dict, List
import copy
import shutil
import ntpath
from string import whitespace

import Utils

_ALIASES_FILENAME = "aliases.txt"

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
        return copy.deepcopy(_ign_uuid_pairs) if do_deepcopy else _ign_uuid_pairs
    _ign_uuid_pairs = {} # key ign, value uuid
    if not os.path.isfile('uuids.txt'):
        return {}
    with open('uuids.txt') as file:
        for line in file:
            words = line.rstrip().split()
            _ign_uuid_pairs[words[0].lower()] = words[1]
    return copy.deepcopy(_ign_uuid_pairs) if do_deepcopy else _ign_uuid_pairs

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

    shutil.copy('uuids.txt', create_file('uuids copy', 'old-uuids'))
    pairs = ign_uuid_pairs_in_uuids_txt(do_deepcopy=True)
    pairs.update(ign_uuid_pairs)
    with open("uuids.txt", "w") as file:
        for key, value in pairs.items():
            file.write(f"{key} {value}\n")
            assert key == key.lower()
    print(f"uuids.txt now contains uuid-ign pairs for {len(pairs)} players.")

def add_aliases(keywords: List[str]) -> None:
    print_aliases('Current aliases:')
    aliases: Dict[str, str] = {a: ' '.join(m) for a,m in get_aliases().items()}
    while True:
        curr_alias = input("Enter alias (or 'done'/'stop' to quit): ").lower()
        if curr_alias in ('done', 'stop', 'quit'):
            break
        if curr_alias in keywords:
            raise ValueError(f'{curr_alias} is a keyword')
        assert not Utils.contains_whitespace(curr_alias)
        curr_meaning = input("Enter the text this alias stands for: ").lower()
        assert '.txt' not in curr_meaning
        if curr_meaning in ('del', 'delete', 'remove'):
            if input(f"Confirm you want to delete the {curr_alias} alias by entering y: ") in ('y', 'Y'):
                del aliases[curr_alias]
            continue
        if curr_alias in aliases:
            print(f"'{curr_alias}' is already an alias that stands for '{aliases[curr_alias]}'. ", end='')
            if input(f"To confirm replacing its meaning to be '{curr_meaning}', enter y: ") not in ('y', 'Y'):
                continue
        aliases[curr_alias] = curr_meaning
        print()

    shutil.copy('aliases.txt', create_file('aliases copy', 'old-aliases'))
    with open(_ALIASES_FILENAME, 'w') as file:
        for a,m in sorted(aliases.items()):
            file.write(f'"{a}" = "{m}"\n')
    print_aliases("\nUpdated aliases:")

def get_aliases() -> Dict[str, List[str]]:
    """ Returns a list representing the aliases stored in aliases.txt. Each element of this list
        will be a tuple, where the first element is a string (the alias), and the second element
        is a list of strings (what the alias stands for). """
    aliases: Dict[str, List[str]] = {}
    if not os.path.isfile(_ALIASES_FILENAME):
        return aliases
    lines: List[str]
    with open(_ALIASES_FILENAME, 'r') as file:
        lines = file.read().splitlines()
    for line in lines:
        split_line = [x.strip(whitespace + '"') for x in line.split('=')]
        assert line.count('=') == 1 and len(split_line) == 2 and line == line.lower()
        aliases[split_line[0]] = split_line[1].split()
    return aliases

def print_aliases(msg: str = 'Aliases:') -> None:
    print(f'{msg}\n')
    for alias in (aliases := get_aliases()):
        print(f"{alias} = {aliases[alias]}")
    print()

def apply_aliases(lst: List[str]) -> List[str]:
    """Returns a new list that results from applying the aliases (in aliases.txt) to the strings in lst."""
    old_lst = lst
    for alias in (aliases := get_aliases()):
        lst = Utils.replace_in_list(lst, alias, aliases[alias])
    # If lst got updated, keep recursing (as some aliases may have aliases of their own):
    return apply_aliases(lst) if lst != old_lst else lst