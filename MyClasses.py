"""This file should only depend on Utils.py."""

from __future__ import annotations

from copy import deepcopy
from typing import Optional, Union

import Utils
import Args

class UUID_Plus_Time:
    """This class encapsulates a UUID and a time (unix epoch), likely representing when
    the player was friended to the parent player."""

    def __init__(self, uuid: str, time_val: Union[str, float, int, None]):
        """time_val must be either a date string, or the unix epoch time in either seconds or milliseconds"""
        self._uuid: str = uuid
        self._unix_epoch_milliseconds: Optional[float] = None
        if isinstance(time_val, str):
            assert Utils.is_date_string(time_val)
            self._unix_epoch_milliseconds = Utils.date_to_epoch(time_val, False)
        elif isinstance(time_val, (float, int)):
            if Utils.is_in_milliseconds(time_val):
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
        return Utils.epoch_to_date(self._unix_epoch_milliseconds, False)

    def sort_key(self) -> float:
        if self._unix_epoch_milliseconds is None:
            return 0
        return -self._unix_epoch_milliseconds

    def refers_to_same_person(self, other: UUID_Plus_Time) -> bool:
        return self._uuid == other.uuid()

    def more_recent(self, other: UUID_Plus_Time) -> bool:
        return (self.time_epoch_in_milliseconds() or 0) > (other.time_epoch_in_milliseconds() or 0)

class Specs:
    """This class represents specifications that a caller has when it calls the
       create_dictionary_report_for_player function."""

    _common_specs: dict = {'print player data': None, 'set flag': False}

    @classmethod
    def set_common_specs(cls, print_player_data: bool) -> None:
        assert not cls._common_specs['set flag']
        cls._common_specs['print player data'] = print_player_data
        cls._common_specs['set flag'] = True

    @classmethod
    def _get_value_for_key(cls, key: str) -> bool:
        assert cls._common_specs[key] is not None and cls._common_specs['set flag']
        return cls._common_specs[key]

    @classmethod
    def make_specs_object_and_initialize_common_specs(cls, args: Args.Args) -> Specs:
        Specs.set_common_specs(not args.find_friends_of_friends())
        friendsfriendsSpecs = Specs(True, False, None, 2) if args.find_friends_of_friends() else None
        friendsSpecs = Specs(args.just_uuids(), args.just_online_friends(), friendsfriendsSpecs, 1)
        playerSpecs = Specs(False, False, friendsSpecs, 0)
        return playerSpecs

    def __init__(self, just_uuids: bool, player_must_be_online: bool,
                 friends_specs: Optional[Specs], degrees_from_original_player: int):
        assert Specs._common_specs['set flag']
        self._just_uuids = just_uuids
        self._player_must_be_online = player_must_be_online
        self._friends_specs = deepcopy(friends_specs)
        self._degrees_from_original_player = degrees_from_original_player

    def just_uuids(self) -> bool:
        return self._just_uuids

    def required_online(self) -> bool:
        return self._player_must_be_online

    def specs_for_friends(self) -> Optional[Specs]:
        return deepcopy(self._friends_specs)

    def degrees_from_root_player(self) -> int:
        return self._degrees_from_original_player

    def root_player(self) -> bool:
        return self._degrees_from_original_player == 0

    def friend_of_root_player(self) -> bool:
        return self._degrees_from_original_player == 1

    def print_player_data_exclude_friends(self) -> bool:
        return Specs._get_value_for_key('print player data') and self.friend_of_root_player()

    def print_only_players_friends(self) -> bool:
        return Specs._get_value_for_key('print player data') and self.root_player()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Specs):
            raise ValueError("'other' is not an instance of Specs")
        return (self.just_uuids() == other.just_uuids() and
                self.degrees_from_root_player() == other.degrees_from_root_player() and
                self.friend_of_root_player() == other.friend_of_root_player() and
                self.required_online() == other.required_online() and
                self.specs_for_friends() == other.specs_for_friends())