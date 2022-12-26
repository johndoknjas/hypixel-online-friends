"""This file should only depend on Utils.py."""

from __future__ import annotations

import datetime
import time
from typing import Optional, List, Union
import Utils

class UUID_Plus_Time:
    """This class encapsulates a UUID and a time (unix epoch), likely representing when
    they were added to another player."""

    @classmethod
    def sort_players_by_time(cls, players: List[UUID_Plus_Time], 
                             more_recent_first: bool = True) -> List[UUID_Plus_Time]:
        """Returns a sorted version of the list, does not modify original."""
        return sorted(players, key=lambda f: f.sort_key(), reverse=more_recent_first)
    
    @classmethod
    def remove_duplicate_players(cls, players: List[UUID_Plus_Time]) -> List[UUID_Plus_Time]:
        """Removes elements with a UUID of an earlier element in the list. Returns this revised version
        of the list, does not modify original."""
        return [f for i, f in enumerate(players) if not any(f.refers_to_same_person(other) for other in players[:i])]
    
    @classmethod
    def exclude_players(cls, players: List[UUID_Plus_Time], 
                        players_to_exclude: Optional[List[UUID_Plus_Time]]) -> List[UUID_Plus_Time]:
        """Removes elements with a UUID appearing in 'players_to_exclude', and returns the new list. Does
        not modify originals of parameters."""
        if not players_to_exclude:
            return players
        return [f for f in players if not any(f.refers_to_same_person(e) for e in players_to_exclude)]
    
    @classmethod
    def remove_players_before_date(cls, players: List[UUID_Plus_Time], 
                                   date_cutoff: Optional[str]) -> List[UUID_Plus_Time]:
        """Removes elements in players with a time value older/less than date_cutoff, 
        and then returns the new list. Does not modify originals of parameters"""

        if not date_cutoff:
            return players
        return [f for f in players if (time_added := f.time_epoch_in_seconds()) and 
                time_added >= time.mktime(datetime.datetime.strptime(date_cutoff, '%Y-%m-%d').timetuple())]
    
    @classmethod
    def prepare_list_for_processing(cls, players: List[UUID_Plus_Time], 
                                    date_cutoff: Optional[str] = None,
                                    exclude_players: Optional[List[UUID_Plus_Time]] = None,
                                    sort_players_by_time: bool = True) -> List[UUID_Plus_Time]:
        players = UUID_Plus_Time.sort_players_by_time(players) if sort_players_by_time else players
        players = UUID_Plus_Time.remove_duplicate_players(players)
        players = UUID_Plus_Time.exclude_players(players, exclude_players)
        return UUID_Plus_Time.remove_players_before_date(players, date_cutoff)

    def __init__(self, uuid: str, time_val: Union[str, float, int, None]):
        """time_val must be either a date string, or the unix epoch time in either seconds or milliseconds"""
        self._uuid: str = uuid
        self._unix_epoch_milliseconds: Optional[float] = None
        if isinstance(time_val, str):
            assert Utils.is_date_string(time_val)
            self._unix_epoch_milliseconds = 1000 * time.mktime(datetime.datetime.strptime(
                                                               time_val, '%Y-%m-%d').timetuple())
        elif isinstance(time_val, float) or isinstance(time_val, int):
            if time_val > 10000000000: # If greater than 10 billion, must already be in ms
                self._unix_epoch_milliseconds = time_val
            else:
                self._unix_epoch_milliseconds = time_val * 1000
    
    def uuid(self) -> str:
        return self._uuid

    def time_epoch_in_seconds(self) -> Optional[float]:
        return self._unix_epoch_milliseconds / 1000 if self._unix_epoch_milliseconds is not None else None
    
    def time_epoch_in_milliseconds(self) -> Optional[float]:
        """Returns the time as a float representing the unix epoch time in milliseconds"""
        return self._unix_epoch_milliseconds
    
    def date_string(self) -> Optional[str]:
        """Returns the time as a YYYY-MM-DD date string"""
        if self._unix_epoch_milliseconds is None:
            return None
        return datetime.datetime.utcfromtimestamp(self._unix_epoch_milliseconds / 1000).strftime('%Y-%m-%d')
    
    def no_time(self) -> bool:
        return self._unix_epoch_milliseconds is None
    
    def sort_key(self) -> float:
        if self._unix_epoch_milliseconds is None:
            return 0
        return self._unix_epoch_milliseconds
    
    def refers_to_same_person(self, other: UUID_Plus_Time) -> bool:
        return self._uuid == other.uuid()

class Specs:
    """This class represents specifications that a caller has when it calls the 
       create_dictionary_report_for_player function."""

    _common_specs: dict = {'print player data': None, 'display time as unix epoch': None, 'set flag': False}
    
    @classmethod
    def set_common_specs(cls, print_player_data: bool, display_time_as_unix_epoch: bool) -> None:
        assert not cls._common_specs['set flag']
        cls._common_specs['print player data'] = print_player_data
        cls._common_specs['display time as unix epoch'] = display_time_as_unix_epoch
        cls._common_specs['set flag'] = True
    
    @classmethod
    def _get_value_for_key(cls, key: str) -> bool:
        assert key in cls._common_specs and cls._common_specs[key] is not None
        return cls._common_specs[key]
    
    @classmethod
    def is_common_specs_initialized(cls) -> bool:
        return cls._get_value_for_key('set flag')
    
    @classmethod
    def does_program_print_player_data(cls) -> bool:
        return cls._get_value_for_key('print player data')
    
    @classmethod
    def does_program_display_time_as_unix_epoch(cls) -> bool:
        return cls._get_value_for_key('display time as unix epoch')

    def __init__(self, include_players_name_and_fkdr: bool, player_must_be_online: bool,
                 friends_specs: Optional[Specs], degrees_from_original_player: int):
        assert Specs._common_specs['set flag']
        self._include_players_name_and_fkdr = include_players_name_and_fkdr
        self._player_must_be_online = player_must_be_online
        self._friends_specs = friends_specs
        self._degrees_from_original_player = degrees_from_original_player
    
    def include_name_fkdr(self) -> bool:
        return self._include_players_name_and_fkdr
    
    def required_online(self) -> bool:
        return self._player_must_be_online
    
    def specs_for_friends(self) -> Optional[Specs]:
        return self._friends_specs
    
    def degrees_from_root_player(self) -> int:
        return self._degrees_from_original_player
    
    def root_player(self) -> bool:
        return self._degrees_from_original_player == 0
    
    def friend_of_root_player(self) -> bool:
        return self._degrees_from_original_player == 1
    
    def print_player_data_exclude_friends(self) -> bool:
        return Specs._common_specs['print player data'] and self.friend_of_root_player()
    
    def print_only_players_friends(self) -> bool:
        return Specs._common_specs['print player data'] and self.root_player()