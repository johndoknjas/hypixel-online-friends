import sys
from typing import List, Optional
from itertools import combinations

import hypixel
from MyClasses import UUID_Plus_Time, Specs
import Utils
import Files
from Player import Player
from copy import deepcopy

def find_dict_for_given_username(d: dict, username: str, uuid: str = None,
                                 make_deep_copy: bool = True) -> Optional[dict]:
    """ d will be a dictionary read from a file in json format - it will have a uuid key, and possibly
    a name, fkdr, and friends key. The friends key would have a value that is a list of dictionaries,
    recursively following the same dictionary requirements."""
    if make_deep_copy:
        d = deepcopy(d)
    if uuid and d['uuid'] == uuid:
        return d
    if 'name' in d and d['name'].lower() == username.lower():
        return d
    elif 'friends' in d:
        for friend_dict in d['friends']:
            if result := find_dict_for_given_username(friend_dict, username, uuid=uuid, make_deep_copy=False):
                return result
    return None

def is_players_friend_list_in_results(player: Player) -> bool:
    """Returns a bool representing if the player's friend list is stored in the results folder, whether
    it be with the player as the main subject of a textfile, or if the player's f list is shown in
    a 'friends of friends' textfile."""
    all_jsons: list[dict] = Files.get_all_jsons_in_results()
    return any(find_dict_for_given_username(json, player.name(), uuid=player.uuid()) for json in all_jsons)

def get_all_players_with_f_list_in_dict(d: dict, make_deepcopy: bool = True) -> list[str]:
    """Returns the uuids of all players who have their f list represented in the dict. The dict is in the
    json format that the textfiles use, so it may be recursive and store multiple f lists."""
    if make_deepcopy:
        d = deepcopy(d)
    if 'friends' in d:
        list_of_players: list[str] = [d['uuid']]
        for friend_dict in d['friends']:
            list_of_players.extend(get_all_players_with_f_list_in_dict(friend_dict, make_deepcopy=False))
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

def make_players_list_from_args(args: List[str], specs: Specs) -> List[Player]:
    """Will return a list of Players, where each Player represents each player referred to by args. """
    date_cutoff: Optional[str] = Utils.get_date_string_if_exists(args)
    args = Utils.remove_date_strings(args)
    info_on_players: List[Player] = []
    encountered_minus_symbol = False
    for i, arg in enumerate(args):
        if arg.endswith('.txt'):
            continue
        if arg == '-':
            encountered_minus_symbol = True
            continue

        player = (make_player_from_textfile_json(args[i+1], arg)
                  if i < len(args) - 1 and args[i+1].endswith('.txt')
                  else Player(hypixel.Player(arg).getUUID()))
        player.set_specs(specs)
        if len(info_on_players) == 0:
            print("The uuid of the player you're getting friends of is " + player.uuid())
            print("This player has " + str(len(player.friends())) + " friends total.")

        player.set_will_exclude_friends(encountered_minus_symbol)
        if not player.will_exclude_friends():
            player.set_date_cutoff_for_friends(date_cutoff)
        info_on_players.append(player)

    return info_on_players

def combine_players(info_on_players: List[Player]) -> Player:
    """This function runs through the Player list and adds/subtracts f lists. Whether a Player's f list
    is used to add or subtract depends on the bool value of their player.will_exclude_friends() function."""
    info_on_players = deepcopy(info_on_players)
    playerNameForFileOutput = info_on_players[0].name()
    playerUUID = info_on_players[0].uuid()
    playerFriends: List[Player] = info_on_players[0].friends()
    playerSpecs = info_on_players[0].specs()
    date_cutoff_friends = info_on_players[0].date_cutoff_for_friends()

    exclude_friends: List[Player] = []
    for player in info_on_players[1:]:
        if player.will_exclude_friends():
            exclude_friends.extend(player.friends())
            playerNameForFileOutput += (' minus ' + player.name())
        else:
            playerFriends.extend(player.friends())
            playerNameForFileOutput += (' plus ' + player.name())

    player = Player(playerUUID, friends=playerFriends, name_for_file_output=playerNameForFileOutput,
                    specs=playerSpecs, date_cutoff_for_friends=date_cutoff_friends)
    player.polish_friends_list(exclude_friends)
    print("Now " + str(len(player.friends())) + " friends after adjustments specified in args.")
    return player

def make_Specs_object(find_friends_of_friends: bool, just_uuids_of_friends: bool, 
                      just_online_friends: bool) -> Specs:
    friendsfriendsSpecs = Specs(False, False, None, 2) if find_friends_of_friends else None
    friendsSpecs = Specs(not just_uuids_of_friends, just_online_friends, friendsfriendsSpecs, 1)
    playerSpecs = Specs(True, False, friendsSpecs, 0)
    return playerSpecs

def diff_f_lists(players: List[Player]) -> None:
    """Runs through all pairs of players and outputs the diff of their f lists"""
    for p1, p2 in combinations(players, 2):
        pass
        # CONTINUE HERE
        # Test program a bit more, but should be good.
        # Implement this diff_f_lists function (never did get around to doing this today...)


def main():
    hypixel.set_api_keys()

    #Files.write_data_as_json_to_file(hypixel.getJSON('counts'), "test online hypixel player count")
    #Files.write_data_as_json_to_file(hypixel.getJSON('leaderboards'), "test leaderboards")

    args = [arg if arg.endswith('.txt') else arg.lower() for arg in sys.argv][1:]
    find_friends_of_friends = 'friendsoffriends' in args
    just_online_friends = 'all' not in args and not find_friends_of_friends
    check_results = 'checkresults' in args
    should_compare_f_lists = 'diff' in args or 'compare' in args

    Specs.set_common_specs(not find_friends_of_friends, 'epoch' in args)
    playerSpecs = make_Specs_object(find_friends_of_friends, 'justuuids' in args, just_online_friends)
    
    args = Utils.list_subtract(args, ['all', 'friendsoffriends', 'justuuids', 'checkresults', 'epoch',
                                      'diff', 'compare'])

    players = make_players_list_from_args(args, playerSpecs)

    if should_compare_f_lists:
        diff_f_lists(players)

    player = combine_players(players)
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