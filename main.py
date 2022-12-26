import sys
from typing import List, Optional

import hypixel
from MyClasses import UUID_Plus_Time, Specs
import Utils
import Files

def set_api_keys() -> None:
    API_KEYS = []
    with open('api-key.txt') as file:
        for line in file:
            API_KEYS.append(line.rstrip())
    hypixel.setKeys(API_KEYS)

def create_player_object(playerName) -> hypixel.Player:
    """Use this function if you're using the player's ign, rather than the uuid."""
    ign_uuid_pairs = Files.get_ign_uuid_pairs() # dict where the key is a player's ign, value is uuid
    return hypixel.Player(ign_uuid_pairs.get(playerName, playerName))

def calculate_fkdr(player: hypixel.Player) -> float:
    if not player.JSON or 'stats' not in player.JSON or 'Bedwars' not in player.JSON['stats']:
        return 0.0
    return Utils.fkdr_division(player.JSON['stats']['Bedwars'].get('final_kills_bedwars', 0), 
                               player.JSON['stats']['Bedwars'].get('final_deaths_bedwars', 0))

def polish_dictionary_report(report: dict, specs: Specs) -> dict:
    if 'friends' in report and all('fkdr' in d for d in report['friends']):
        report['friends'] = sorted(report['friends'], key=lambda d: d['fkdr'], reverse=True)
    if (friends_specs := specs.specs_for_friends()) and friends_specs.required_online():
        report['friends'] = remove_players_who_logged_off(report['friends'])
    if specs.print_only_players_friends():
        print('\n\n')
        Utils.print_list_of_dicts(report['friends'])
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
        player_report['time'] = (player_info.time_epoch_in_milliseconds() 
                                 if Specs.does_program_display_time_as_unix_epoch() 
                                 else player_info.date_string())
    if specs.print_player_data_exclude_friends():
        print(str(player_report))

    if not (specs_for_friends := specs.specs_for_friends()):
        return player_report
    # Now to use recursion to make a list of dictionaries for the player's friends, which will be the value
    # of this 'friends' key in the player's dictionary:
    if friends is None:
        friends = player.getFriends()
    player_report['friends'] = []
    for i, friend in enumerate(friends):
        if specs.root_player() and i % 20 == 0:
            print("Processed " + str(i))
        if report := create_dictionary_report_for_player(friend, specs_for_friends):
            player_report['friends'].append(report)

    if specs.root_player():
        player_report = polish_dictionary_report(player_report, specs)

    return player_report

def remove_players_who_logged_off(players: List[dict]) -> List[dict]:
    return [p for p in players if hypixel.Player(p['uuid']).isOnline()]

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

def is_players_friend_list_in_results(username: str) -> bool:
    """Returns a bool representing if the player's friend list is stored in the results folder, whether
    it be with the player as the main subject of a textfile, or if the player's f list is shown in
    a 'friends of friends' textfile."""
    all_jsons: list[dict] = Files.get_all_jsons_in_results()
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
    all_jsons: list[dict] = Files.get_all_jsons_in_results()
    all_players_with_f_list_in_results: list[str] = []
    for json in all_jsons:
        all_players_with_f_list_in_results.extend(get_all_players_with_f_list_in_dict(json))
    return len(Utils.remove_duplicates(all_players_with_f_list_in_results))

def get_player_json_from_textfile(relative_filepath: str, username: str) -> dict:
    dict_from_file = Files.read_json_textfile(relative_filepath)
    dict_for_player = find_dict_for_given_username(dict_from_file, username)
    assert dict_for_player
    dict_for_player['friends'] = [UUID_Plus_Time(d['uuid'], d.get('time', None))
                                  for d in dict_for_player.pop('friends')]
    return dict_for_player

def process_args(args: List[str]) -> List[dict]:
    """Will return a list of dicts, where each dict has info for each player referred to by args. """
    args = Utils.remove_date_strings(args)
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
    playerFriends = UUID_Plus_Time.prepare_list_for_processing(
        playerFriends, date_cutoff=Utils.get_date_string_if_exists(args), exclude_players=exclude_friends)

    print("Now " + str(len(playerFriends)) + " friends after adjustments specified in args.")

    return {'playerUUID': playerUUID, 'playerFriends': playerFriends,
            'playerNameForFileOutput': playerNameForFileOutput}

def make_Specs_object(find_friends_of_friends: bool, just_uuids_of_friends: bool, 
                      just_online_friends: bool) -> Specs:
    friendsfriendsSpecs = Specs(False, False, None, 2) if find_friends_of_friends else None
    friendsSpecs = Specs(not just_uuids_of_friends, just_online_friends, friendsfriendsSpecs, 1)
    playerSpecs = Specs(True, False, friendsSpecs, 0)
    return playerSpecs

def main():
    set_api_keys()

    #Files.write_data_as_json_to_file(hypixel.getJSON('counts'), "test online hypixel player count")
    #Files.write_data_as_json_to_file(hypixel.getJSON('leaderboards'), "test leaderboards")

    args = [arg if arg.endswith('.txt') else arg.lower() for arg in sys.argv][1:]
    find_friends_of_friends = 'friendsoffriends' in args
    just_online_friends = 'all' not in args and not find_friends_of_friends
    check_results = 'checkresults' in args

    Specs.set_common_specs(not find_friends_of_friends, 'epoch' in args)
    playerSpecs = make_Specs_object(find_friends_of_friends, 'justuuids' in args, just_online_friends)
    
    args = Utils.list_subtract(args, ['all', 'friendsoffriends', 'justuuids', 'checkresults', 'epoch'])

    player_info = get_players_info_from_args(args)
    if check_results:
        print("There are " + str(num_players_with_f_lists_in_results()) + " players with their f list in results.")
        print("It's " + str(is_players_friend_list_in_results(player_info['playerNameForFileOutput'])).lower()
              + " that " + player_info['playerNameForFileOutput'] + "'s friends list is in the results folder.")
    report = create_dictionary_report_for_player(UUID_Plus_Time(player_info['playerUUID'], None), playerSpecs, 
                                                 player_info['playerFriends'])

    if not just_online_friends:
        filename = ("Friends of " + ("friends of " if find_friends_of_friends else "") 
                    + player_info['playerNameForFileOutput'])
        Files.write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()