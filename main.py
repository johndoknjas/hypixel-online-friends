import os
import os.path
import sys
import time
import datetime
import json
from collections import OrderedDict
from typing import List, Union, Optional

import hypixel
from MyClasses import UUID_Plus_Time, Specs

# CONTINUE HERE - todos:

    # Add a feature to just get friends over a certain fkdr.
        # When this is implemented you could then run the program and save this list a file, and then 
        # just go through this file when looking for people to party online.

    # Add a feature where if 'avg' is a command line argument, the average size will be calculated for
    # all friends lists the program comes across. Could also make a 'total' arg, that displays the total
    # number of (unique) friends in all f lists processed.

    # Add a feature that aims to backup the friends lists of most of the (active part?) of the hypixel server.
        # A good way to do this is use the hypixel api to get players on the daily bedwars leaderboard.
        # This will update every day, and the people on the leaderboard are obviously active players who
        # probably are friends with other active players.

        # So could go through each daily leaderboard, pick the top 10, get their 10 most recently added friends,
        # get their 10 most recently added friends, etc until something like 1000-10,000. You can backup these
        # many friends lists then.
            # Important that before continuing down this "tree" at a given player, you check that their
            # f list is not already backed up in the results folder.
                # When doing this, can also record how many of these players already have their f lists
                # recorded in the results folder. This
                # can give you an idea as time goes on of approx. what percentage of f lists of active bw
                # players you've backed up.
                    # At the time of writing this percentage should be pretty low though, since it's under 10,000
                    # players' f lists recorded in results.

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

def remove_duplicates(lst: List) -> List:
    return list(OrderedDict.fromkeys(lst)) # regular dict works to maintain order for python >= 3.7

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
    """Use this function if you're using the player's ign, rather than the uuid."""
    ign_uuid_pairs = get_ign_uuid_pairs() # dict where the key is a player's ign, value is uuid
    return hypixel.Player(ign_uuid_pairs.get(playerName, playerName))

def calculate_fkdr(player: hypixel.Player) -> float:
    if not player.JSON or 'stats' not in player.JSON or 'Bedwars' not in player.JSON['stats']:
        return 0.0
    return fkdr_division(player.JSON['stats']['Bedwars'].get('final_kills_bedwars', 0), 
                         player.JSON['stats']['Bedwars'].get('final_deaths_bedwars', 0))

def polish_dictionary_report(report: dict, specs: Specs) -> dict:
    if 'friends' in report and all('fkdr' in d for d in report['friends']):
        report['friends'] = sorted(report['friends'], key=lambda d: d['fkdr'], reverse=True)
    if specs.specs_for_friends() and specs.specs_for_friends().required_online():
        report['friends'] = remove_players_who_logged_off(report['friends'])
    if specs.print_only_players_friends():
        print('\n\n')
        print_list_of_dicts(report['friends'])
    return report

def create_dictionary_report_for_player(player_info: UUID_Plus_Time, specs: Specs,
                                        friends: Optional[List[UUID_Plus_Time]] = None) -> dict:
    """Creates a dictionary representing info for a player. This dictionary will be ready to be written to a
    file as a json.
    If a value is given for the friends argument, then it will be used, rather than
    calling the API to get player's friends. This can be done if the caller wants to exclude some friends.
    'player' will represent the player's uuid, and possibly a time (for when the player and parent player of
    this function call became friends). If player is the root player, then there will be no time represented,
    since there's no parent player. """

    if specs.root_player():
        assert player_info.no_time()

    if (specs.include_name_fkdr() or specs.required_online() or
        (specs.specs_for_friends() and friends is None)):
        player = hypixel.Player(player_info.uuid())
    if specs.required_online() and not player.isOnline():
        return {}

    player_report = {}
    if specs.include_name_fkdr():
        player_report.update({'name': player.getName(), 'fkdr': calculate_fkdr(player)})
    player_report['uuid'] = player_info.uuid()
    if not player_info.no_time():
        player_report['time'] = player_info.time_epoch_in_milliseconds()
    if specs.print_player_data_exclude_friends():
        print(str(player_report))

    if not specs.specs_for_friends():
        return player_report
    # Now to use recursion to make a list of dictionaries for the player's friends, which will be the value
    # of this 'friends' key in the player's dictionary:
    if friends is None:
        friends = player.getFriends()
    player_report['friends'] = []
    for i, friend in enumerate(friends):
        if specs.root_player() and i % 20 == 0:
            print("Processed " + str(i))
        if report := create_dictionary_report_for_player(friend, specs.specs_for_friends()):
            player_report['friends'].append(report)

    if specs.root_player():
        player_report = polish_dictionary_report(player_report, specs)

    return player_report

def remove_players_who_logged_off(players: List[dict]) -> List[dict]:
    return [p for p in players if hypixel.Player(p['uuid']).isOnline()]

def print_list_of_dicts(lst: List[dict]) -> None:
    print("\n".join([str(d) for d in lst]))

def write_data_as_json_to_file(data: dict, description: str = "") -> None:
    filename = os.path.join("results", description + " - " + str(time.time_ns()) + ".txt")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(json.dumps(data, indent=4))

def find_dict_for_given_username(d: dict, username: str) -> Optional[dict]:
    # d will be a dictionary read from a file in json format - it will have a uuid key, and possibly
    # a name, fkdr, and friends key. The friends key would have a value that is a list of dictionaries,
    # recursively following the same dictionary requirements.
    if 'name' in d and d['name'].lower() == username.lower():
        return d
    elif 'friends' in d:
        for friend_dict in d['friends']:
            if result := find_dict_for_given_username(friend_dict, username):
                return result
    return None

def get_all_jsons_in_results() -> list[dict]:
    """Returns a list of dicts, where each dict represents the json each textfile stores."""
    all_jsons: list[dict] = []
    all_files = os.listdir('results')
    all_files = [f for f in all_files if f.startswith('Friends of') and f.endswith('.txt')]
    for f in all_files:
        filename = os.path.join('results', f)
        all_jsons.append(read_json_textfile(filename))
    return all_jsons

def is_players_friend_list_in_results(username: str) -> bool:
    """Returns a bool representing if the player's friend list is stored in the results folder, whether
    it be with the player as the main subject of a textfile, or if the player's f list is shown in
    a 'friends of friends' textfile."""
    all_jsons: list[dict] = get_all_jsons_in_results()
    return any(find_dict_for_given_username(json, username) for json in all_jsons)

def get_all_players_with_f_list_in_dict(d: dict) -> list[str]:
    """Returns the uuids of all players who have their f list represented in the dict. The dict is in the
    json format that the textfiles use, so it may be recursive and store multiple f lists."""
    if 'friends' in d:
        list_of_players: list[str] = [d['uuid']]
        for friend_dict in d['friends']:
            list_of_players.extend(get_all_players_with_f_list_in_dict(friend_dict))
        return list_of_players
    else:
        return []

def num_players_with_f_lists_in_results() -> int:
    """Returns the number of unique players who have their f lists stored in the results folder."""
    all_jsons: list[dict] = get_all_jsons_in_results()
    all_players_with_f_list_in_results: list[str] = []
    for json in all_jsons:
        all_players_with_f_list_in_results.extend(get_all_players_with_f_list_in_dict(json))
    return len(remove_duplicates(all_players_with_f_list_in_results))

def read_json_textfile(relative_filepath: str) -> dict:
    with open(relative_filepath, 'r') as f:
        dict_from_file = json.loads(f.read())
    return dict_from_file

def get_player_json_from_textfile(relative_filepath: str, username: str) -> dict:
    dict_from_file = read_json_textfile(relative_filepath)
    dict_for_player = find_dict_for_given_username(dict_from_file, username)
    assert dict_for_player
    dict_for_player['friends'] = [UUID_Plus_Time(d['uuid'], unix_epoch_milliseconds=d.get('time', None))
                                  for d in dict_for_player.pop('friends')]
    return dict_for_player

def process_args(args: List[str]) -> List[dict]:
    """Will return a list of dicts, where each dict has info for each player referred to by args. """
    args = remove_arguments_no_longer_needed(args)
    info_of_players: List[dict] = []
    encountered_minus_symbol = False
    for i, arg in enumerate(args):
        if arg.endswith('.txt'):
            continue
        if arg == '-':
            encountered_minus_symbol = True
            continue

        if i < len(args) - 1 and args[i+1].endswith('.txt'):
            player_info = get_player_json_from_textfile(args[i+1], arg)
        else:
            player = create_player_object(arg)
            player_info = {'name': player.getName(), 'uuid': player.getUUID(),
                           'friends': list(reversed(player.getFriends()))
                          }
        player_info['exclude'] = encountered_minus_symbol
        info_of_players.append(player_info)

    return info_of_players

def sort_friends_and_remove_duplicates(friends: List[UUID_Plus_Time]) -> List[UUID_Plus_Time]:
    """Each dict in friends should have two key-value pairs, representing a friend's uuid 
       and the time they were added. The dicts in the list will be sorted by date, and the same friend
       appearing (so two dicts with the same uuid key-value pair) will be removed. """
    
    friends = sorted(friends, key=lambda f: f.sort_key(), reverse=True)
    return [f for i, f in enumerate(friends) if not any(f.same_person(other) for other in friends[:i])]

def get_players_info_from_args(args: List[str]) -> dict:
    info_on_players: List[dict] = process_args(args)
    playerNameForFileOutput = info_on_players[0]['name']
    playerUUID = info_on_players[0]['uuid']
    playerFriends: List[UUID_Plus_Time] = info_on_players[0]['friends']

    print("fyi, the uuid of the player you're getting friends of is " + playerUUID)
    print("This player has " + str(len(playerFriends)) + " friends total.")

    exclude_friends: List[UUID_Plus_Time] = []
    for player in info_on_players[1:]:
        if player['exclude']:
            exclude_friends.extend(player['friends'])
            playerNameForFileOutput += (' minus ' + player['name'])
        else:
            playerFriends.extend(player['friends'])
            playerNameForFileOutput += (' plus ' + player['name'])
    playerFriends = sort_friends_and_remove_duplicates(playerFriends)
    playerFriends = [f for f in playerFriends if not any(f.same_person(e) for e in exclude_friends)]
    if friend_add_time_cutoff := get_date_if_exists(args):
        playerFriends = [f for f in playerFriends if f.time_epoch_in_milliseconds() >= friend_add_time_cutoff]

    print("Now " + str(len(playerFriends)) + " friends after adjustments specified in args.")

    return {'playerUUID': playerUUID, 'playerFriends': playerFriends,
            'playerNameForFileOutput': playerNameForFileOutput}

def remove_date_strings(lst: List[str]) -> None:
    return [x for x in lst if not get_date_if_exists(x)]

def get_date_if_exists(args: Union[List[str], str]) -> Optional[float]:
    """If no date strings found, return None. Otherwise, convert the first date string found into 
    unix epoch time (milliseconds), and return it."""
    if isinstance(args, str):
        args = [args]
    for arg in args:
        try:
            date = datetime.datetime.strptime(arg, '%Y-%m-%d')
        except ValueError:
            continue
        return time.mktime(date.timetuple()) * 1000
    return None

def remove_arguments_no_longer_needed(args: List[str]) -> List[str]:
    return list_subtract(remove_date_strings(args[1:]), ['all', 'friendsoffriends', 'justuuids', 'checkresults'])

def make_Specs_object(find_friends_of_friends: bool, just_uuids_of_friends: bool, 
                      just_online_friends: bool) -> Specs:
    if not Specs.is_common_specs_initialized():
        Specs.set_common_specs(not find_friends_of_friends)
    friendsfriendsSpecs = Specs(False, False, None, 2) if find_friends_of_friends else None
    friendsSpecs = Specs(not just_uuids_of_friends, just_online_friends, friendsfriendsSpecs, 1)
    playerSpecs = Specs(True, False, friendsSpecs, 0)
    return playerSpecs

def main():
    set_api_keys()

    #write_data_as_json_to_file(hypixel.getJSON('counts'), "test online hypixel player count")
    #write_data_as_json_to_file(hypixel.getJSON('leaderboards'), "test leaderboards")

    args = [arg if arg.endswith('.txt') else arg.lower() for arg in sys.argv]
    just_uuids_of_friends = 'justuuids' in args
    find_friends_of_friends = 'friendsoffriends' in args
    just_online_friends = 'all' not in args and not find_friends_of_friends
    check_results = 'checkresults' in args
    player_info: dict = get_players_info_from_args(args)
    if check_results:
        print("There are " + str(num_players_with_f_lists_in_results()) + " players with their f list in results.")
        print("It's " + str(is_players_friend_list_in_results(player_info['playerNameForFileOutput'])).lower()
              + " that " + player_info['playerNameForFileOutput'] + "'s friends list is in the results folder.")
    
    playerSpecs = make_Specs_object(find_friends_of_friends, just_uuids_of_friends, just_online_friends)
    report = create_dictionary_report_for_player(UUID_Plus_Time(player_info['playerUUID']), playerSpecs, 
                                                 player_info['playerFriends'])

    if not just_online_friends:
        filename = ("Friends of " + ("friends of " if find_friends_of_friends else "") 
                    + player_info['playerNameForFileOutput'])
        write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()