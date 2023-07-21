import sys
from typing import List, Tuple
from itertools import combinations
from copy import deepcopy

import hypixel
from MyClasses import Specs, UUID_Plus_Time
import Files
from Player import Player
from Args import Args
import ProcessingResults
import additional_friends
import Utils

def intersect_player_lists(l1: List[Player], l2: List[Player]) -> List[Player]:
    return [p for p in l1 if p.in_player_list(l2)]

def combine_players(info_on_players: List[Player]) -> Player:
    """This function runs through the Player list and adds/subtracts/intersects f lists. Whether a Player's f list
    is used to add/subtract/intersect depends on the bool value of their player.will_exclude_friends() 
    and player.will_intersect() functions.
    If a player's f list is used to intersect, it will intersect the entire friends list up to that point,
    either for playerFriends or exclude_friends. 
    Order of operations:
        union, intersect (left to right for precedence amongst these)
        subtract
    """
    info_on_players = deepcopy(info_on_players)
    playerNameForFileOutput = info_on_players[0].name()
    playerUUID = info_on_players[0].uuid()
    playerFriends: List[Player] = info_on_players[0].friends()
    playerSpecs = info_on_players[0].specs()
    date_cutoff_friends = info_on_players[0].date_cutoff_for_friends()

    exclude_friends: List[Player] = []
    for player in info_on_players[1:]:
        if player.will_exclude_friends():
            if player.will_intersect():
                exclude_friends = intersect_player_lists(exclude_friends, player.friends())
                playerNameForFileOutput += (' intersect ' + player.name())
            else:
                exclude_friends.extend(player.friends())
                playerNameForFileOutput += (' minus ' + player.name())
        else:
            if player.will_intersect():
                playerFriends = intersect_player_lists(playerFriends, player.friends())
                playerNameForFileOutput += (' intersect ' + player.name())
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

def get_players_from_args(args: Args) -> Tuple[List[Player], List[str]]:
    """The first item in the tuple will be a list of Players.
       The second item will likely be empty for most use cases. However, if the user wants this feature,
       it will be a list if uuid strings, where it's intended for each uuid to be checked for when they
       were friended by a Player in the first list."""

    specs = Specs.make_specs_object_and_initialize_common_specs(args)
    args_no_keywords_or_date = args.get_args(True, True)
    players: List[Player] = []
    in_minus_symbol_section = False
    in_friended_when_section = False
    is_intersect_player = False
    FROM_RESULTS = 'fromresults'
    FRIENDED_WHEN = 'friendedwhen'
    INTERSECT = 'intersect'
    uuids_for_friended_when: List[str] = []

    for i, arg in enumerate(args_no_keywords_or_date):
        if arg.endswith('.txt') or arg == FROM_RESULTS:
            assert not in_friended_when_section
            continue
        if arg == '-':
            in_minus_symbol_section = True
            assert not in_friended_when_section
            continue
        if arg == FRIENDED_WHEN:
            in_friended_when_section = True
            in_minus_symbol_section = False
            continue
        if arg == INTERSECT:
            is_intersect_player = True
            assert not in_friended_when_section
            continue

        if in_friended_when_section:
            uuids_for_friended_when.append(hypixel.get_uuid(arg))
            continue

        next_arg = args_no_keywords_or_date[i+1] if i+1 < len(args_no_keywords_or_date) else None
        use_specific_textfile = next_arg and next_arg.endswith('.txt')
        use_results_folder = args.from_results_for_all() or next_arg == FROM_RESULTS

        player = None
        if use_specific_textfile:
            assert not args.do_file_output()
            player = Player.make_player_from_json_textfile(args_no_keywords_or_date[i+1], arg, specs=specs)
        elif use_results_folder:
            hypixel_obj = hypixel.Player(arg)
            uuid = hypixel_obj.getUUID()
            all_friends: List[UUID_Plus_Time] = []
            standard_friends = ProcessingResults.get_best_f_list_for_player_in_results(uuid,
            must_have_times_friended=(FRIENDED_WHEN in args_no_keywords_or_date))
            if args.get_additional_friends():
                print("total number of friends in biggest single friends list/file for " + arg +
                      (" (" + hypixel_obj.getName() + ")" if Utils.is_uuid(arg) else "") +
                      ": " + str(len(standard_friends)))
                all_friends = ProcessingResults.get_all_additional_friends_for_player(uuid)
                print("total number of 'additional friends' is " + str(len(all_friends)))
                for f in standard_friends:
                    ProcessingResults.update_list_if_applicable(all_friends, f)
            else:
                all_friends = standard_friends
            all_friends.sort(key=UUID_Plus_Time.sort_key)
            player = Player(uuid, specs=specs, friends=all_friends, hypixel_object=hypixel_obj)
        else:
            player = Player(hypixel.get_uuid(arg), specs=specs)

        if Utils.is_ign(arg):
            print("This player's uuid is " + player.uuid())
        print("This player has " + str(len(player.friends())) + " unique friends total.\n")

        player.set_will_exclude_friends(in_minus_symbol_section)
        player.set_will_intersect(is_intersect_player)
        if not player.will_exclude_friends():
            player.set_date_cutoff_for_friends(args.date_cutoff())
        players.append(player)
        is_intersect_player = False

    return (players, uuids_for_friended_when)

def main():
    hypixel.set_api_keys()

    args = Args(sys.argv)
    if args.add_additional_friends():
        additional_friends.add_additional_friends_to_file_system(args.get_args(True, True)[0])
        sys.exit(0)
    if args.add_aliases():
        Files.add_aliases(args.get_keywords())
        sys.exit(0)

    ProcessingResults.set_args(args)
    if args.find_matching_igns_or_uuids_in_results():
        ProcessingResults.print_all_matching_uuids_or_igns(args.get_args(True, True)[0])
    players_from_args, uuids_for_friended_when = get_players_from_args(args)
    if args.diff_left_to_right() or args.diff_right_to_left():
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

    for friend in player.friends():
        if friend.uuid() in uuids_for_friended_when:
            print(friend.name() + " was friended on " + friend.time_friended_parent_player('date'))

    report = player.create_dictionary_report(sort_final_result_by_fkdr = not args.sort_by_star(),
                                             should_terminate=(args.do_file_output() or
                                                               not args.just_online_friends()))
    if args.do_file_output():
        assert (args.date_cutoff() is None and not args.just_online_friends() and not args.minus_results())
        filename = ("Friends of " + 
                    ("friends of " if args.find_friends_of_friends() else "") + 
                    player.name_for_file_output())
        Files.write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()