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
import Pit
import leveling
import bedwars
import Graphing
from Graphing import ScatterplotInfo

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

    print(f"Now {len(player.friends())} friends after adjustments specified in args.\n\n")

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
        if in_minus_symbol_section or in_friended_when_section or is_intersect_player:
            assert not args.do_mini_program()

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
        num_friends_msgs = ['', '']

        if use_specific_textfile:
            assert not args.do_file_output()
            player = Player.make_player_from_json_textfile(args_no_keywords_or_date[i+1], arg, specs=specs)
        elif use_results_folder:
            hypixel_obj = hypixel.Player(arg)
            uuid = hypixel_obj.getUUID()
            all_friends: List[UUID_Plus_Time] = []
            standard_friends = ProcessingResults.get_best_f_list_for_player_in_results(
                uuid, must_have_times_friended=FRIENDED_WHEN in args_no_keywords_or_date
            )
            num_friends_msgs[0] = f"{len(standard_friends)} friends in biggest single friends list/file\n"
            if args.get_additional_friends():
                all_friends = ProcessingResults.get_all_additional_friends_for_player(uuid)
                num_friends_msgs[1] = (f"{len(all_friends)} unique 'additional friends'\n")
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
        Player.print_dict_report(player.get_stats_dict(), player.network_rank(), True)
        print(num_friends_msgs[0] + num_friends_msgs[1], end='')
        player.print_player_info()

        player.set_will_exclude_friends(in_minus_symbol_section)
        player.set_will_intersect(is_intersect_player)
        if not player.will_exclude_friends():
            player.set_date_cutoff_for_friends(args.date_cutoff())
        players.append(player)
        is_intersect_player = False

    return (players, uuids_for_friended_when)

def output_player_jsons_to_file(players: List[Player]) -> None:
    for player in players:
        Files.write_data_as_json_to_file(player.player_JSON(), "Player json for " + player.name(), 
                                         "results/player-jsons")
        
def friended_when_feature(players: List[Player], uuids_for_friended_when: List[str]) -> None:
    for player in players:
        for friend in player.friends():
            if friend.uuid() not in uuids_for_friended_when:
                continue
            time_friended = friend.time_friended_parent_player('date')
            if time_friended is not None:
                assert type(time_friended) is str
                print(f'{player.name()} became friends with {friend.name()} on {time_friended}')
            else:
                print(f'{player.name()} is friends with {friend.name()}, but no date recorded.')

def set_args_in_files(args: Args) -> None:
    ProcessingResults.set_args(args)
    hypixel.set_verify_requests(args.verify_requests())

def do_mini_program(args: Args) -> None:
    if args.add_additional_friends():
        additional_friends.add_additional_friends_to_file_system(args.get_args(True, True)[0])
    elif args.add_aliases():
        Files.add_aliases(args.get_keywords())
    elif args.print_aliases():
        print(*sorted(f"{a} --> {' '.join(l)}" for a,l in Files.get_aliases()), sep='\n')
    elif args.get_player_json():
        output_player_jsons_to_file(get_players_from_args(args)[0])
    elif args.pit_percent():
        for arg in args.get_args(True, True):
            Pit.PitStats(Pit.get_xp_req_for_rank(arg)).print_info()
    elif args.pit_plot():
        fig1 = ScatterplotInfo(Pit.xp_percent_levels(), range(1, 121), 'Levels',
                               'XP % Through a Prestige', 'Level')
        prestige_xps = Pit.PRESTIGE_XP[:50]
        fig2 = ScatterplotInfo(prestige_xps, range(1, len(prestige_xps)+1),
                               'XP vs Prestige', 'XP', 'Prestige')
        Graphing.output_scatterplots((fig1, fig1.invert(), fig2, fig2.invert()))
    elif args.network_plot():
        level_range = range(1, 1001)
        fig = ScatterplotInfo((leveling.getTotalExpToLevelFloor(l) for l in level_range), level_range,
                              "XP vs Network Level", "XP", "Level")
        fig_inverted = fig.invert()
        print(f"level vs xp data fit to a quadratic: {fig_inverted.fit_to_polynomial(2)}\n")
        Graphing.output_scatterplots((fig, fig_inverted))
    elif args.bedwars_plot():
        print("Note that for some players, they may get to some levels with slightly less xp "
              "than required on the graph. Not exactly sure why this is. Made a bug report to "
              "hypixel, see if they get back to you with a reason for it.")
        level_range = range(0, 3001)
        fig = ScatterplotInfo(level_range, (bedwars.totalExpForLevel(l) for l in level_range),
                              "Bedwars Level vs XP", "Level", "XP")
        print(f"\nlevel vs xp data fit to a linear function: {fig.fit_to_polynomial(1)}\n")
        Graphing.output_scatterplots([fig])
    elif args.contains_substr():
        for substr in args.get_args(False, False)[1:]:
            substr = substr.lower()
            keyword_matches = sorted([keyword for keyword in args.get_keywords()
                                      if substr in keyword.lower()])
            print(f"Keyword matches for '{substr}':\n" + '\n'.join(keyword_matches))
            ign_matches = sorted([ign for ign in ProcessingResults.ign_uuid_pairs_in_results()
                                  if substr in ign.lower()])
            print(f"\nPlayer name matches for '{substr}':\n" + '\n'.join(ign_matches) + '\n')
    else:
        assert False

def main() -> None:
    args = Args(sys.argv)
    set_args_in_files(args)

    if args.do_mini_program():
        do_mini_program(args)
        sys.exit(0)

    if args.find_matching_igns_or_uuids_in_results():
        ProcessingResults.print_all_matching_uuids_or_igns(args.get_args(True, True)[0])
    players_from_args, uuids_for_friended_when = get_players_from_args(args)
    if args.diff_left_to_right() or args.diff_right_to_left():
        diff_f_lists(players_from_args, args)
    if uuids_for_friended_when:
        friended_when_feature(players_from_args, uuids_for_friended_when)

    player = combine_players(players_from_args)

    if args.check_results():
        ProcessingResults.check_results(player.uuid(), player.name())
        if args.minus_results():
            player.polish_friends_list({uuid: Player(uuid) for uuid in 
                                        ProcessingResults.player_uuids_with_f_list_in_results()})
            print(f"Now {len(player.friends())} unique friends after applying 'minusresults'.")

    if args.update_uuids():
        Files.update_uuids_file(ProcessingResults.ign_uuid_pairs_in_results())

    report = player.create_dictionary_report(
        sort_key = "star" if args.sort_by_star() else "pit_rank" if args.sort_by_pit_rank() else "fkdr",
        should_terminate = args.do_file_output() or not args.just_online_friends()
    )
    if args.do_file_output():
        filename = ("Friends of " + 
                    ("friends of " if args.find_friends_of_friends() else "") + 
                    player.name_for_file_output())
        Files.write_data_as_json_to_file(report, filename)

if __name__ == '__main__':
    main()