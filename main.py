import sys
from typing import List
from itertools import combinations
from copy import deepcopy
import operator

import hypixel
from MyClasses import Specs, UUID_Plus_Time
import Files
from Player import Player
from Args import Args
import ProcessingResults
import Utils
import additional_friends

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
        FROM_RESULTS = 'fromresults'
        if arg.endswith('.txt') or arg == FROM_RESULTS:
            continue
        if arg == '-':
            encountered_minus_symbol = True
            continue

        use_specific_textfile = Utils.cmp_element_val(args_no_keywords_or_date, i+1, '.txt', str.endswith)
        use_results_folder = (args.from_results_for_all() or 
                              Utils.cmp_element_val(args_no_keywords_or_date, i+1, FROM_RESULTS, operator.eq))

        player = None
        if use_specific_textfile:
            player = Player.make_player_from_json_textfile(args_no_keywords_or_date[i+1], arg, specs=specs)
        elif use_results_folder:
            uuid = hypixel.Player(arg).getUUID()
            all_friends: List[UUID_Plus_Time] = []
            standard_friends = ProcessingResults.get_largest_f_list_for_player_in_results(uuid)
            if args.get_additional_friends():
                print("total number of unique standard friends (without additional friends) for " +
                      arg + ": " + str(len(standard_friends)))
                all_friends = ProcessingResults.get_all_additional_friends_for_player(uuid)
                print("total number of unique additional friends is " + str(len(all_friends)))
                for f in standard_friends:
                    ProcessingResults.update_list_if_applicable(all_friends, f)
            else:
                all_friends = standard_friends
            all_friends.sort(key=UUID_Plus_Time.sort_key)
            player = Player(uuid, specs=specs, friends=all_friends)
        else:
            player = Player(hypixel.Player(arg).getUUID(), specs=specs)

        if i == 0:
            print("The uuid of the player you're getting friends of is " + player.uuid())
            print("This player has " + str(len(player.friends())) + " unique friends total.")

        player.set_will_exclude_friends(encountered_minus_symbol)
        if not player.will_exclude_friends():
            player.set_date_cutoff_for_friends(args.date_cutoff())
        players.append(player)

    return players

def main():
    hypixel.set_api_keys()

    args = Args(sys.argv)
    if args.add_additional_friends():
        additional_friends.add_additional_friends_to_file_system(args.get_args(True, True)[0])
        sys.exit(0)
    ProcessingResults.set_args(args)
    if args.find_matching_igns_or_uuids_in_results():
        ProcessingResults.print_all_matching_uuids_or_igns(args.get_args(True, True)[0])
    players_from_args = get_players_from_args(args)
    diff_f_lists(players_from_args, args)
    player = combine_players(players_from_args)
    if args.check_results():
        ProcessingResults.check_results(player, not args.get_trivial_dicts_in_results())
        if args.minus_results():
            player.polish_friends_list({uuid: Player(uuid) for uuid in 
                                        ProcessingResults.player_uuids_with_f_list_in_results()})
            print("Now " + str(len(player.friends())) + " unique friends after applying 'minusresults'.")

    if args.update_uuids():
        Files.update_uuids_file(ProcessingResults.ign_uuid_pairs_in_results())

    report = player.create_dictionary_report(sort_final_result_by_fkdr = not args.sort_by_star())
    if args.do_file_output():
        filename = ("Friends of " + 
                    ("friends of " if args.find_friends_of_friends() else "") + 
                    player.name_for_file_output() + 
                    (", added after " + date if (date := args.date_cutoff()) else ""))
        Files.write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()