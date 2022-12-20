from __future__ import annotations
import os
import os.path
import sys
from hypixelpy import hypixel
import time
from typing import List, Union, Optional
import json

# CONTINUE HERE - todos:

    # Maybe do an overlay.

    # Add a feature to just get friends over a certain fkdr.
        # When this is implemented you could then run the program and save this list a file, and then 
        # just go through this file when looking for people to party online.
    
    # Add a feature to just get friends who were added since a given date or more recently.

    # Add a feature to get friends of 2+ accounts/textfile lists.

# This class represents specifications that a caller has when it calls the create_dictionary_report_for_player
# function.
class Specs:
    def __init__(self, include_players_name_and_fkdr: bool, player_must_be_online: bool, 
                 friends_specs: Optional[Specs]):
        self.include_players_name_and_fkdr = include_players_name_and_fkdr
        self.player_must_be_online = player_must_be_online
        self.friends_specs = friends_specs

def fkdr_division(final_kills: int, final_deaths: int) -> float:
    return final_kills / final_deaths if final_deaths else float(final_kills)

def set_api_keys() -> None:
    API_KEYS = []
    with open('api-key.txt') as file:
        for line in file:
            API_KEYS.append(line.rstrip())
    hypixel.setKeys(API_KEYS)

def list_subtract(main_list: List, subtract_list: List) -> List:
    return [x for x in main_list if x not in subtract_list]

def get_ign_uuid_pairs() -> dict:
    if not os.path.isfile('uuids.txt'):
        return {}
    ign_uuid_pairs = {} # key ign, value uuid
    with open('uuids.txt') as file:
        for line in file:
            words = line.rstrip().split()
            ign_uuid_pairs[words[0].lower()] = words[1]
    return ign_uuid_pairs

def create_player_object(playerName) -> hypixel.Player:
    # Use this function if you're using the player's ign, rather than the uuid.
    ign_uuid_pairs = get_ign_uuid_pairs() # dict where the key is a player's ign, value is uuid
    return hypixel.Player(ign_uuid_pairs.get(playerName, playerName))

def calculate_fkdr(player: hypixel.Player) -> float:
    if 'stats' not in player.JSON or 'Bedwars' not in player.JSON['stats']:
        return 0.0
    return fkdr_division(player.JSON['stats']['Bedwars'].get('final_kills_bedwars', 0), 
                         player.JSON['stats']['Bedwars'].get('final_deaths_bedwars', 0))

def polish_dictionary_report(report: dict, friends_specs: Specs, print_friends_to_screen: bool) -> dict:
    if 'friends' in report and all('fkdr' in d for d in report['friends']):
        report['friends'] = sorted(report['friends'], key=lambda d: d['fkdr'], reverse=True)
    if friends_specs and friends_specs.player_must_be_online:
        report['friends'] = remove_players_who_logged_off(report['friends'])
    if print_friends_to_screen:
        print('\n\n')
        print_list_of_dicts(report['friends'])
    return report

def create_dictionary_report_for_player(playerUUID: str, specs_player: Specs, degrees_from_original_player: int,
                                        print_friends_to_screen: bool,
                                        friendsUUIDs: Optional[List[str]] = None) -> dict:
    """Creates a dictionary representing info for a player. This dictionary will be ready to be written to a
    file as a json."""
    if (specs_player.include_players_name_and_fkdr or specs_player.player_must_be_online or
        (specs_player.friends_specs and not friendsUUIDs)):
        player = hypixel.Player(playerUUID)
    if specs_player.player_must_be_online and not player.isOnline():
        return {}

    player_data = {}
    if specs_player.include_players_name_and_fkdr:
        player_data['name'] = player.getName()
        player_data['fkdr'] = calculate_fkdr(player)
    player_data['uuid'] = playerUUID
    if degrees_from_original_player == 1 and print_friends_to_screen:
        print(str(player_data))

    if not specs_player.friends_specs:
        return player_data
    # Now to use recursion to make a list of dictionaries for the player's friends, which will be the value
    # of this 'friends' key in the player's dictionary:
    friendsUUIDs = friendsUUIDs or player.getUUIDsOfFriends()
    player_data['friends'] = []
    for i, friendUUID in enumerate(friendsUUIDs):
        if degrees_from_original_player == 0 and i % 20 == 0:
            print("Processed " + str(i))
        if report := create_dictionary_report_for_player(friendUUID, specs_player.friends_specs, 
                                                         degrees_from_original_player + 1, print_friends_to_screen):
            player_data['friends'].append(report)

    if degrees_from_original_player == 0:
        player_data = polish_dictionary_report(player_data, specs_player.friends_specs, print_friends_to_screen)

    return player_data

def remove_players_who_logged_off(players: List[dict]) -> List[dict]:
    return [p for p in players if hypixel.Player(p['uuid']).isOnline()]

def print_list_of_dicts(lst: List[dict]) -> None:
    print("\n".join([str(d) for d in lst]))

def write_data_as_json_to_file(data: Union[dict, List], description: str = "") -> None:
    filename = os.path.join("results", description + " - " + str(time.time_ns()) + ".txt")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(json.dumps(data, indent=4))

def find_dict_for_given_username(d: dict, username: str) -> dict:
    # d will be a dictionary read from a file in json format - it will have a uuid key, and possibly
    # a name, fkdr, and friends key. The friends key would have a value that is a list of dictionaries,
    # recursively following the same dictionary requirements.
    if 'name' in d and d['name'].lower() == username.lower():
        return d
    elif 'friends' in d:
        for friend_dict in d['friends']:
            if result := find_dict_for_given_username(friend_dict, username):
                return result
    else:
        return None

def read_json_textfile(relative_filepath: str, username: str) -> dict:
    with open(relative_filepath, 'r') as f:
        dict_from_file = json.loads(f.read())
    dict_for_player = find_dict_for_given_username(dict_from_file, username)
    assert dict_for_player
    dict_for_player['friends'] = [d['uuid'] for d in dict_for_player['friends']]
    dict_for_player['friends_uuids'] = dict_for_player.pop('friends')
    return dict_for_player

def process_args(args: List[str]) -> List[dict]:
    """args must only contain at least 1 ign string, and 0 or more .txt filenames. For any .txt filenames, they
    must come immediately after the ign they correspond to.
    Will return a list of dicts, where each dict has info for each player referred to by args. """
    info_of_players: List[dict] = []
    for i, arg in enumerate(args):
        if arg.endswith('.txt'):
            continue
        if i < len(args) - 1 and args[i+1].endswith('.txt'):
            info_of_players.append(read_json_textfile(args[i+1], arg))
        else:
            player = create_player_object(arg)
            info_of_players.append(
                {
                    'name': player.getName(), 
                    'uuid': player.getUUID(),
                    'friends_uuids': list(reversed(player.getUUIDsOfFriends()))
                }
            )
    return info_of_players

def main():
    set_api_keys()

    args = [arg if arg.endswith('.txt') else arg.lower() for arg in sys.argv]
    just_uuids_of_friends = 'justuuidsoffriends' in args
    find_friends_of_friends = 'friendsoffriends' in args
    just_online_friends = 'all' not in args and not find_friends_of_friends
    args = list_subtract(args[1:], ['all', 'friendsoffriends', 'justuuidsoffriends'])

    info_on_players: List[dict] = process_args(args)
    playerName = info_on_players[0]['name']
    playerUUID = info_on_players[0]['uuid']
    playerFriendsUUIDS = info_on_players[0]['friends_uuids']

    print("fyi, the uuid of the player you're getting friends of is " + playerUUID)
    print("This player has " + str(len(playerFriendsUUIDS)) + " friends total.")

    for player_subtract in info_on_players[1:]:
        friendsExclude = player_subtract['friends_uuids']
        playerFriendsUUIDS = list_subtract(playerFriendsUUIDS, friendsExclude)
    
    friendsfriendsSpecs = Specs(False, False, None) if find_friends_of_friends else None
    friendsSpecs = Specs(not just_uuids_of_friends, just_online_friends, friendsfriendsSpecs)
    playerSpecs = Specs(True, False, friendsSpecs)
    report = create_dictionary_report_for_player(playerUUID, playerSpecs, 0, not find_friends_of_friends,
                                                 playerFriendsUUIDS)
    filename = "Friends of " + ("friends of " if find_friends_of_friends else "") + playerName
    write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()