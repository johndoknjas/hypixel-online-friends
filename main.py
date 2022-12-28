import sys
from typing import List, Optional

import hypixel
from MyClasses import UUID_Plus_Time, Specs
import Utils
import Files
from Player import Player

def find_dict_for_given_username(d: dict, username: str, uuid: str = None) -> Optional[dict]:
    # d will be a dictionary read from a file in json format - it will have a uuid key, and possibly
    # a name, fkdr, and friends key. The friends key would have a value that is a list of dictionaries,
    # recursively following the same dictionary requirements.
    if uuid and d['uuid'] == uuid:
        return d
    if 'name' in d and d['name'].lower() == username.lower():
        return d
    elif 'friends' in d:
        for friend_dict in d['friends']:
            if result := find_dict_for_given_username(friend_dict, username, uuid=uuid):
                return result
    return None

def is_players_friend_list_in_results(player: Player) -> bool:
    """Returns a bool representing if the player's friend list is stored in the results folder, whether
    it be with the player as the main subject of a textfile, or if the player's f list is shown in
    a 'friends of friends' textfile."""
    all_jsons: list[dict] = Files.get_all_jsons_in_results()
    return any(find_dict_for_given_username(json, player.name(), uuid=player.uuid()) for json in all_jsons)

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

def make_player_from_textfile_json(relative_filepath: str, username: str) -> Player:
    dict_from_file = Files.read_json_textfile(relative_filepath)
    dict_for_player = find_dict_for_given_username(dict_from_file, username)
    assert dict_for_player
    return Player(uuid=dict_for_player['uuid'], 
                  friends=[
                            UUID_Plus_Time(d['uuid'], d.get('time', None))
                            for d in dict_for_player.pop('friends')
                          ]
                 )

def process_args(args: List[str], specs: Specs) -> List[Player]:
    """Will return a list of Players, where each Player represents each player referred to by args. """
    args = Utils.remove_date_strings(args)
    info_on_players: List[Player] = []
    encountered_minus_symbol = False
    for i, arg in enumerate(args):
        if arg.endswith('.txt'):
            continue
        if arg == '-':
            encountered_minus_symbol = True
            continue

        if i < len(args) - 1 and args[i+1].endswith('.txt'):
            player = make_player_from_textfile_json(args[i+1], arg)
        else:
            player = Player(hypixel.Player(arg).getUUID())
        player.set_exclude_friends(encountered_minus_symbol)
        player.set_specs(specs)
        info_on_players.append(player)

    return info_on_players

def get_players_info_from_args(args: List[str], specs: Specs) -> Player:
    info_on_players: List[Player] = process_args(args, specs)
    playerNameForFileOutput = info_on_players[0].name()
    playerUUID = info_on_players[0].uuid()
    playerFriends: List[Player] = info_on_players[0].friends()
    playerSpecs = info_on_players[0].specs()

    print("fyi, the uuid of the player you're getting friends of is " + playerUUID)
    print("This player has " + str(len(playerFriends)) + " friends total.")

    exclude_friends: List[Player] = []
    for player in info_on_players[1:]:
        if player.exclude_friends():
            exclude_friends.extend(player.friends())
            playerNameForFileOutput += (' minus ' + player.name())
        else:
            playerFriends.extend(player.friends())
            playerNameForFileOutput += (' plus ' + player.name())

    player = Player(playerUUID, friends=playerFriends, name_for_file_output=playerNameForFileOutput,
                    specs=playerSpecs)
    player.polish_friends_list(Utils.get_date_string_if_exists(args), exclude_friends)
    print("Now " + str(len(player.friends())) + " friends after adjustments specified in args.")
    return player

def make_Specs_object(find_friends_of_friends: bool, just_uuids_of_friends: bool, 
                      just_online_friends: bool) -> Specs:
    friendsfriendsSpecs = Specs(False, False, None, 2) if find_friends_of_friends else None
    friendsSpecs = Specs(not just_uuids_of_friends, just_online_friends, friendsfriendsSpecs, 1)
    playerSpecs = Specs(True, False, friendsSpecs, 0)
    return playerSpecs

def main():
    hypixel.set_api_keys()

    #Files.write_data_as_json_to_file(hypixel.getJSON('counts'), "test online hypixel player count")
    #Files.write_data_as_json_to_file(hypixel.getJSON('leaderboards'), "test leaderboards")

    args = [arg if arg.endswith('.txt') else arg.lower() for arg in sys.argv][1:]
    find_friends_of_friends = 'friendsoffriends' in args
    just_online_friends = 'all' not in args and not find_friends_of_friends
    check_results = 'checkresults' in args

    Specs.set_common_specs(not find_friends_of_friends, 'epoch' in args)
    playerSpecs = make_Specs_object(find_friends_of_friends, 'justuuids' in args, just_online_friends)
    
    args = Utils.list_subtract(args, ['all', 'friendsoffriends', 'justuuids', 'checkresults', 'epoch'])

    player = get_players_info_from_args(args, playerSpecs)
    if check_results:
        print("There are " + str(num_players_with_f_lists_in_results()) + " players with their f list in results.")
        print("It's " + str(is_players_friend_list_in_results(player)).lower()
              + " that " + player.name() + "'s friends list is in the results folder.")
    report = player.create_dictionary_report()

    if not just_online_friends:
        filename = ("Friends of " + ("friends of " if find_friends_of_friends else "") 
                    + player.name_for_file_output())
        Files.write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()