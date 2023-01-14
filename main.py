import sys
from typing import List, Optional
from itertools import combinations
from copy import deepcopy

import hypixel
from MyClasses import Specs
import Utils
import Files
from Player import Player
from Args import Args

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

def check_results(player: Optional[Player]) -> List[str]:
    """Traverses through the results folder and prints some stats and info. If a Player object is provided
    for player, then some specific info about them will be outputted as well.
    Also, a list of uuids for players who have their f list stored in the results folder will be returned.
    The caller doesn't have to use it, but it may be useful. """

    all_dicts: list[dict] = Files.get_all_dicts_unique_uuids_in_results()

    print("\n" + str(len(all_dicts)) + " total unique uuids recorded in the results folder.")
    keys = ['friends', 'name', 'fkdr', 'star']
    all_dicts = [d for d in all_dicts if any(k in d for k in keys)]
    print(str(len(all_dicts)) + " total players with non-trivial data stored in the results folder.")

    player_uuids_with_f_list_in_results: List[str] = []

    for k in keys:
        dicts_with_key = [d for d in all_dicts if k in d]
        indent = "  "
        Utils.print_info_for_key(dicts_with_key, k, indent)
        if k != 'friends':
            continue
        player_uuids_with_f_list_in_results = [d['uuid'] for d in dicts_with_key]
        if player:
            print(indent*2 + "Also, it's " + 
                  Utils.bool_lowercase_str(player.uuid() in player_uuids_with_f_list_in_results) +
                  " that " + player.name() + "'s friends list is in the results folder.")
    print('\n\n')
    return player_uuids_with_f_list_in_results

def main():
    hypixel.set_api_keys()

    args = Args(sys.argv)
    players_from_args = get_players_from_args(args)
    diff_f_lists(players_from_args, args)
    player = combine_players(players_from_args)
    if args.check_results():
        player_uuids_with_f_list_in_results = check_results(player)
        if args.minus_results():
            player.polish_friends_list({uuid: Player(uuid) for uuid in player_uuids_with_f_list_in_results})
            print("Now " + str(len(player.friends())) + " friends after applying 'minusresults'.")
    if args.update_uuids():
        Files.update_uuids_file()

    report = player.create_dictionary_report(sort_final_result_by_fkdr=not args.sort_by_star())
    if args.do_file_output():
        filename = ("Friends of " + 
                    ("friends of " if args.find_friends_of_friends() else "") + 
                    player.name_for_file_output() + 
                    (", added after " + date if (date := args.date_cutoff()) else ""))
        Files.write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()