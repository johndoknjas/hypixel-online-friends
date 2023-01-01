import sys
from typing import List
from itertools import combinations
from copy import deepcopy

import hypixel
from MyClasses import Specs
import Utils
import Files
from Player import Player
from Args import Args

def is_players_friend_list_in_results(player: Player) -> bool:
    """Returns a bool representing if the player's friend list is stored in the results folder, whether
    it be with the player as the main subject of a textfile, or if the player's f list is shown in
    a 'friends of friends' textfile."""
    all_jsons: list[dict] = Files.get_all_jsons_in_results()
    return any(Utils.find_dict_for_given_username(json, player.name(), uuid=player.uuid()) for json in all_jsons)

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

def diff_f_lists(players: List[Player], args: Args) -> None:
    """Runs through all pairs of players and outputs the diff of their f lists"""
    for p1, p2 in combinations(players, 2):
        if args.diff_left_to_right():
            p1.diff_f_lists(p2, print_results=True)
        if args.diff_right_to_left():
            p2.diff_f_lists(p1, print_results=True)

def get_players_from_args(args: Args) -> List[Player]:
    specs = Specs.make_specs_object_and_initialize_common_specs(args)
    args_no_keywords_or_date = args.get_args(True, True)
    players: List[Player] = []
    encountered_minus_symbol = False

    for i, arg in enumerate(args_no_keywords_or_date):
        if arg.endswith('.txt'):
            continue
        if arg == '-':
            encountered_minus_symbol = True
            continue

        player = (Player.make_player_from_json_textfile(args_no_keywords_or_date[i+1], arg, specs=specs)
                if i < len(args_no_keywords_or_date) - 1 and args_no_keywords_or_date[i+1].endswith('.txt')
                else Player(hypixel.Player(arg).getUUID(), specs=specs))
        if len(players) == 0:
            print("The uuid of the player you're getting friends of is " + player.uuid())
            print("This player has " + str(len(player.friends())) + " friends total.")

        player.set_will_exclude_friends(encountered_minus_symbol)
        if not player.will_exclude_friends():
            player.set_date_cutoff_for_friends(args.date_cutoff())
        players.append(player)

    return players

def main():
    hypixel.set_api_keys()

    #Files.write_data_as_json_to_file(hypixel.getJSON('counts'), "test online hypixel player count")
    #Files.write_data_as_json_to_file(hypixel.getJSON('leaderboards'), "test leaderboards")

    args = Args(sys.argv, ['all', 'friendsoffriends', 'justuuids', 'checkresults', 'epoch',
                           'diff', 'diffl', 'diffr', 'sortstar', 'sortbystar', 'starsort',
                           'nofileoutput'])
    players_from_args = get_players_from_args(args)
    diff_f_lists(players_from_args, args)
    player = combine_players(players_from_args)
    if args.check_results():
        print("There are " + str(num_players_with_f_lists_in_results()) + " players with their f list in results.")
        print("It's " + str(is_players_friend_list_in_results(player)).lower()
              + " that " + player.name() + "'s friends list is in the results folder.")

    report = player.create_dictionary_report(not args.sort_by_star())
    if args.do_file_output():
        filename = ("Friends of " + ("friends of " if args.find_friends_of_friends() else "") 
                    + player.name_for_file_output())
        Files.write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()