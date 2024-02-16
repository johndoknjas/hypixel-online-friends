from __future__ import annotations

from typing import Optional, List, Union, Dict
from copy import deepcopy

import Utils
import hypixel
from MyClasses import UUID_Plus_Time, Specs
import Files
from Pit import PitStats
import ProcessingResults
import leveling
from datetime import datetime

class Player:

    @classmethod
    def make_player_from_json_textfile(cls, filepath: str, uuid_or_ign: str, 
                                       specs: Optional[Specs] = None) -> Player:
        dict_from_file = Files.read_json_textfile(filepath)
        dict_for_player = Utils.find_dict_for_given_player(dict_from_file, uuid_or_ign)
        if not dict_for_player and Utils.is_ign(uuid_or_ign):
            # Possible nothing was found since the given json only contains the uuid for the player,
            # and not their ign. So try again by passing in their uuid.
            dict_for_player = Utils.find_dict_for_given_player(dict_from_file, 
                                                               hypixel.get_uuid(uuid_or_ign))
        assert dict_for_player
        return Player(uuid=dict_for_player['uuid'], 
                      friends=[
                                  UUID_Plus_Time(d['uuid'], d.get('time', None))
                                  for d in dict_for_player.get('friends', [])
                              ],
                      specs=specs
                     )

    def __init__(self, uuid: str, time_friended_parent_player: Union[str, float, int, None] = None,
                 hypixel_object: Optional[hypixel.Player] = None, name: Optional[str] = None, 
                 friends: Union[List[UUID_Plus_Time], List[Player], None] = None, specs: Optional[Specs] = None,
                 name_for_file_output: Optional[str] = None, will_exclude_friends: bool = False,
                 date_cutoff_for_friends: Optional[str] = None, will_intersect: bool = False):
        self._uuid_plus_time = UUID_Plus_Time(uuid, time_friended_parent_player)
        self._hypixel_object = hypixel_object
        self._name = name
        self._specs = deepcopy(specs)
        self._name_for_file_output = name_for_file_output
        self._will_exclude_friends = will_exclude_friends
        self._will_intersect = will_intersect
        self._date_cutoff_for_friends = date_cutoff_for_friends
        self._friends: Optional[List[Player]] = None
        self._call_api_if_friends_empty_in_friends_getter: bool = True
        self._pit_stats: Optional[PitStats] = None
        if friends is not None:
            self._set_friends(friends)
    
    def hypixel_object(self) -> hypixel.Player:
        if not self._hypixel_object:
            self._hypixel_object = hypixel.Player(self.uuid())
        return self._hypixel_object
    
    def pit_stats_object(self) -> PitStats:
        if not self._pit_stats:
            self._pit_stats = PitStats(self.hypixel_object().getPitXP())
        return self._pit_stats
    
    def player_JSON(self) -> dict:
        return self.hypixel_object().JSON

    def uuid(self) -> str:
        return self._uuid_plus_time.uuid()
    
    def time_friended_parent_player(self, date_format: str) -> Union[str, float, int, None]:
        """date_format must be 'ms', 's' or 'date'
        Function will return the time the player friended the parent player. 
        If there is no parent player (e.g., if player is the root player), None is returned."""
        if date_format == 'ms':
            return self._uuid_plus_time.time_epoch_in_milliseconds()
        elif date_format == 's':
            return self._uuid_plus_time.time_epoch_in_seconds()
        elif date_format == 'date':
            return self._uuid_plus_time.date_string()
        else:
            raise ValueError("Invalid value for 'date_format' parameter.")
    
    def name(self) -> str:
        if not self._name:
            self._name = self.hypixel_object().getName()
        return self._name
    
    def name_for_file_output(self) -> str:
        assert self._name_for_file_output is not None
        return self._name_for_file_output
    
    def set_name_for_file_output(self, name: str) -> None:
        self._name_for_file_output = name

    def friends(self) -> List[Player]:
        if not self._friends and self._call_api_if_friends_empty_in_friends_getter:
            self._set_friends(self.hypixel_object().getFriends())
        return self._friends if self._friends is not None else []
    
    def specs(self) -> Specs:
        assert self._specs is not None
        return deepcopy(self._specs)
    
    def root_player(self) -> bool:
        return self.specs().root_player()
    
    def friend_of_root_player(self) -> bool:
        return self.specs().friend_of_root_player()
    
    def get_fkdr(self) -> float:
        return self.hypixel_object().getFKDR()
    
    def get_bw_star(self) -> int:
        return self.hypixel_object().getBedwarsStar()
    
    def get_bw_xp(self) -> int:
        return self.hypixel_object().getBedwarsXP()
    
    def pit_rank_string(self) -> str:
        return self.pit_stats_object().rank_string()
    
    def get_network_level(self) -> float:
        return self.hypixel_object().getExactNWLevel()
    
    def get_network_xp(self) -> int:
        return self.hypixel_object().getNetworkXP()
    
    def get_network_rank(self) -> hypixel.Rank:
        return self.hypixel_object().getNetworkRank()
    
    def percent_way_to_next_network_level(self) -> float:
        return leveling.getPercentageToNextLevel(self.get_network_xp())
    
    def percent_way_overall_to_given_network_level(self, target_level: int) -> float:
        return self.get_network_xp() / leveling.getTotalExpToLevelFloor(target_level)
    
    def specs_for_friends(self) -> Optional[Specs]:
        return self.specs().specs_for_friends()
    
    def represents_same_person(self, other: Player) -> bool:
        return self.uuid() == other.uuid()
    
    def set_specs(self, specs: Specs) -> None:
        self._specs = specs
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Player):
            raise ValueError("'other' is not an instance of Player.")
        return (len(self.friends()) == len(other.friends()) and self.name() == other.name() and 
                self._specs == other._specs and self.uuid() == other.uuid() and
                self.time_friended_parent_player('date') == other.time_friended_parent_player('date'))
    
    def set_date_cutoff_for_friends(self, date_cutoff: Optional[str]) -> None:
        """Sets self._date_cutoff_for_friends to the param, and then applies it to the friends list"""
        if date_cutoff:
            assert not self.will_exclude_friends()
        self._date_cutoff_for_friends = date_cutoff
        self.remove_friends_added_before_cutoff()
    
    def date_cutoff_for_friends(self) -> Optional[str]:
        return self._date_cutoff_for_friends
    
    def remove_friends_added_before_cutoff(self) -> None:
        assert not self.will_exclude_friends()
        if not self._date_cutoff_for_friends or not self._friends:
            return
        self._friends = [f for f in self._friends if not
                         Utils.is_older(f.time_friended_parent_player('s'), self._date_cutoff_for_friends)]
    
    def remove_duplicate_friends(self) -> None:
        """Precondition: friends list must be sorted in the order you want, since duplicates coming after any
        originals will be removed. By a 'duplicate', this means a Player object with the same uuid."""
        assert self._friends is not None
        self._set_friends([f for i, f in enumerate(self.friends()) if not f.in_player_list(self.friends()[:i])])
    
    def _set_friends(self, friends: Union[List[UUID_Plus_Time], List[Player], None]) -> None:
        """Note that after this function has been called, if self.friends() is called later and
        self._friends happens to be None or [], the hypixel api won't be called to populate self._friends. 
        The reasoning for this is that since self._set_friends() is being called now, it's assumed the
        caller wants self._friends to be equal to a certain value -- and None or [] are valid values
        if that's what the caller wants."""

        self._call_api_if_friends_empty_in_friends_getter = False
        if not friends:
            self._friends = None if friends is None else []
            # Above line instead of direct assignment in order to satisfy mypy.
            return
        self._friends = []
        for friend in deepcopy(friends):
            if isinstance(friend, UUID_Plus_Time):
                self._friends.append(Player(friend.uuid(),
                                            time_friended_parent_player=friend.time_epoch_in_seconds()))
            else:
                self._friends.append(friend)
            specs_for_friends = self.specs_for_friends()
            assert isinstance(specs_for_friends, Specs)
            self._friends[len(self._friends)-1].set_specs(specs_for_friends)
        if not self.will_exclude_friends():
            self.remove_friends_added_before_cutoff()
    
    def will_exclude_friends(self) -> bool:
        """Returns whether this player's friends are meant to be excluded, as specified in command line args."""
        return self._will_exclude_friends
    
    def set_will_exclude_friends(self, exclude_friends: bool) -> None:
        if exclude_friends:
            assert not self._date_cutoff_for_friends
        self._will_exclude_friends = exclude_friends
    
    def will_intersect(self) -> bool:
        """Returns whether this player's friends will be intersected with the friends (or exclude friends) 
           list leading up to it in combine_players."""
        return self._will_intersect

    def set_will_intersect(self, will_intersect: bool) -> None:
        self._will_intersect = will_intersect
    
    def in_player_list(self, players: List[Player]) -> bool:
        """Returns whether the player is already represented in this players list."""
        return any(self.represents_same_person(p) for p in players)
    
    @staticmethod
    def print_dict_report(report: Dict, rank: Optional[hypixel.Rank] = None) -> None:
        import Colours
        report = deepcopy(report)
        assert all(isinstance(v, (str,float,int)) for v in report.values())
        possible_keys = ('name', 'fkdr', 'star', 'pit_rank', 'uuid', 'time')
        assert set(report.keys()) <= set(possible_keys)
        name, fkdr, star, pit_rank, uuid, time = [report.get(k) for k in possible_keys]
        assert isinstance(uuid, str) # for mypy

        if name is not None:
            assert isinstance(name, str)
            if old_name := ProcessingResults.uuid_ign_pairs_in_results().get(uuid, ''):
                old_name = '' if old_name.lower() == name.lower() else f' ({old_name})'
            print_length = (len(rank.rank(True)) if rank else 0) + len(name) + len(old_name)
            print(' ' * max(0, 38 - print_length), end='')
            if rank and rank.rank(True):
                rank.print_rank()
                assert (name_colour := rank.name_and_bracket_colour())
                Colours.colour_print(Colours.ColourSpecs(name, name_colour))
            else:
                print(name, end='')
            print(old_name, end='')
        if fkdr is not None:
            magnitude = len(str(int(fkdr := round(fkdr, 3))))
            print(f" {fkdr:.3f}".ljust(6) + " fkdr".ljust(7-magnitude), end='')
        if star is not None:
            Colours.print_bw_star(star)
        if pit_rank is not None:
            Colours.print_pit_rank(pit_rank)
        print(f" uuid {uuid[:(show := 5)]}...{uuid[-show:]}".ljust(10+show*2), end='')
        if time is not None:
            if Utils.is_date_string(time):
                date_obj = datetime.strptime(time, '%Y-%m-%d')
                time = date_obj.strftime('%b ') + date_obj.strftime('%d/%y').lstrip('0')
            print(f" friended {time}", end='')
        print()

    def print_player_info(self) -> None:
        print(f"This player has {len(self.friends())} unique friends total.\n")
        nw_level = self.get_network_level()
        closest_multiple_50 = Utils.round_up_to_closest_multiple(nw_level, 50)
        percent_to_next_level = round(self.percent_way_to_next_network_level() * 100, 2)
        print(f"network xp: {self.get_network_xp()}, network level: {round(nw_level, 3)}, ", end="")
        print(f"{percent_to_next_level}% of the way to the next network level")
        for x in range(0,3):
            multiple_50 = closest_multiple_50 + x*50
            percent_overall_next_50_multiple = Utils.percentify(
                self.percent_way_overall_to_given_network_level(multiple_50)
            )
            print(f"{percent_overall_next_50_multiple} of the way overall to level {multiple_50}, ", end="")
        print("\n")
        print(f"bw fkdr: {self.get_fkdr()}, bw star: {self.get_bw_star()}, bw xp: {self.get_bw_xp()}\n")
        self.pit_stats_object().print_info()
        print("------------------------\n\n")
    
    def create_dictionary_report(self, sort_key: str = "fkdr", extra_online_check: bool = False, 
                                 should_terminate: bool = True) -> dict:
        # CONTINUE HERE - later, could make a Report class and return an object of that, instead of a dict here.
        if self.root_player():
            assert not self.time_friended_parent_player('date')
        if (self.specs().required_online() and 
            not self.hypixel_object().isOnline(extra_online_check=extra_online_check)):
            return {}

        report = {}
        if not self.specs().just_uuids():
            report.update({'name': self.name(), 'fkdr': self.get_fkdr(), 'star': self.get_bw_star(),
                           'pit_rank': self.pit_rank_string()})
        report['uuid'] = self.uuid()
        if time := self.time_friended_parent_player('ms' if Specs.does_program_display_time_as_unix_epoch() 
                                                    else 'date'):
            report['time'] = time
        if self.specs().print_player_data_exclude_friends():
            self.print_dict_report(
                report, self.get_network_rank() if not self.specs().just_uuids() else None
            )
        if not self.specs_for_friends():
            return report
        
        self.iterate_over_friends_for_report(report, self.friends(), not should_terminate, 
                                             sort_key, False, True)

        return (self.polish_dictionary_report(report, sort_key, self.friends()) 
                if self.root_player() else report)
    
    def iterate_over_friends_for_report(self, report: dict, friends: List[Player],
                                        do_additional_passes: bool, sort_key: str,
                                        on_perpetual_pass: bool, on_first_pass: bool,
                                        end_index: Optional[int] = None) -> None:
        """Will modify `report`, which is passed by reference."""

        # For friends whose online status is shown, there will be some false negatives over time.
        # This is because if their json shows them not online at the start of the program, it won't
        # double check if they're currently online.

        # For friends whose online status isn't shown, there will be some false positives over time.
        # This is because a player's stats could have been updated, but then later on they logged out.

        assert not (on_first_pass and on_perpetual_pass)
        if do_additional_passes:
            assert on_first_pass and self.root_player()

        if 'friends' not in report:
            report['friends'] = [] # list of dicts
        points_to_do_second_passes = [200 * 2**i for i in range(0, 10)]

        for i in range(len(friends) if end_index is None else end_index+1):
            if i in points_to_do_second_passes and on_first_pass and do_additional_passes:
                # Do a 'second pass' from 0 until i-1 indexed players, checking if their stats
                # have been updated (for players who don't have the online status shown):
                self.iterate_over_friends_for_report(report, friends, False, sort_key,
                                                     False, False, end_index=i-1)
            assert isinstance(report['friends'], list)
            friend: Player = friends[i]
            if friend.uuid() not in [d['uuid'] for d in report['friends']]:
                if friend_report := friend.create_dictionary_report(extra_online_check = not on_first_pass):
                    report['friends'].append(friend_report)
            self.processed_msg(i+1, on_perpetual_pass, on_first_pass)

        if do_additional_passes and friends:
            # Do perpetual passes:
            while True:
                self.polish_dictionary_report(report, sort_key, friends)
                report['friends'] = []
                self.iterate_over_friends_for_report(report, friends, False,
                                                     sort_key, True, False)
    
    def processed_msg(self, num_processed: int, on_perpetual_pass: bool, on_first_pass: bool) -> None:
        """Prints a message saying how many players have been processed, if the number is a multiple of 50,
           and if the player is the root player."""
        if num_processed % 50 != 0 or not self.root_player():
            return
        msg = f"Processed {num_processed}" + (
            " for a perpetual pass\n" if on_perpetual_pass else
            " for a 'second pass'\n" if not on_first_pass else "\n"
        )
        import Colours
        Colours.colour_print(Colours.ColourSpecs(msg, Colours.Hex.DARK_GRAY))

    def polish_dictionary_report(self, report: dict, sort_key: str, friends: List[Player]) -> dict:
        report = deepcopy(report)
        if not report.get('friends', None): # if friends list doesn't exist or is empty:
            return report
        report['friends'] = sorted(report['friends'], key=lambda d: self._sort_func(d, sort_key),
                                   reverse=True)
        # Assert that there are no duplicate uuids:
        assert report['friends'] == list({f['uuid']:f for f in report['friends']}.values())
        if self.specs().print_only_players_friends():
            print()
            uuid_friend_map = {f.uuid():f for f in friends}
            for d in report['friends']:
                friend = uuid_friend_map[d['uuid']]
                self.print_dict_report(
                    d, friend.get_network_rank() if not friend.specs().just_uuids() else None
                )
            print()
        return report
    
    def _sort_func(self, d: dict, sort_key: str) -> int:
        if sort_key == "pit_rank":
            return Utils.pit_rank_to_num_for_sort(d.get("pit_rank", "0-1"))
        return d.get(sort_key, 0)
    
    def polish_friends_list(self, friends_to_exclude: Union[List[Player], Dict[str, Player]]) -> None:
        """Will sort friends, remove duplicates, and remove any who appear in the friends_to_exclude param.
        Note that a Player object is treated as an equivalent/duplicate player if it has the same uuid as
        another Player. Other details (such as time friended parent player) can differ."""
        assert self._friends is not None
        self.remove_friends_added_before_cutoff() # Probably redundant
        self._set_friends(sorted(self.friends(), key=lambda f: f.time_friended_parent_player('s') or 0, reverse=True))
        self.remove_duplicate_friends()
        if isinstance(friends_to_exclude, List):
            self._set_friends([f for f in self.friends() if not f.in_player_list(friends_to_exclude)])
        elif isinstance(friends_to_exclude, dict):
            self._set_friends([f for f in self.friends() if not f.uuid() in friends_to_exclude])
        else:
            raise ValueError("friends_to_exclude must be a list or dict of Players")
    
    def diff_f_lists(self, other: Player, print_results: bool = False) -> List[Player]:
        diff = [f for f in self.friends() if not f.in_player_list(other.friends())]
        if print_results:
            print(str(len(diff)) + " friends of " + self.name() + " and not of " + other.name() + ":")
            for player in diff:
                player.print_uuid_name()
            print('\n\n')
        return diff
    
    def print_uuid_name(self) -> None:
        print('name: ' + self.name() + ', uuid: ' + self.uuid())