from __future__ import annotations

from typing import Optional, List, Union

import Utils
import hypixel
from MyClasses import UUID_Plus_Time, Specs
import datetime
import time

class Player:

    @classmethod
    def remove_duplicates(cls, players: List[Player]) -> List[Player]:
        return [p for i, p in enumerate(players) if not 
                any(p.represents_same_person(other) for other in players[:i])]
    
    @classmethod
    def remove_players_friended_to_parent_before_date(cls, players: List[Player], 
                                                      date_cutoff: Optional[str]) -> List[Player]:
        if not date_cutoff:
            return players
        return [p for p in players if (time_added := p.time_friended_parent_player('s')) and 
                time_added >= time.mktime(datetime.datetime.strptime(date_cutoff, '%Y-%m-%d').timetuple())]

    def __init__(self, uuid: str, time_friended_parent_player: Union[str, float, int, None] = None,
                 hypixel_object: Optional[hypixel.Player] = None, name: str = None, 
                 friends: Optional[List[Union[UUID_Plus_Time, Player]]] = None, specs: Optional[Specs] = None,
                 name_for_file_output: Optional[str] = None, exclude_friends: Optional[bool] = None):
        self._uuid_plus_time = UUID_Plus_Time(uuid, time_friended_parent_player)
        self._hypixel_object = hypixel_object
        self._name = name
        self._specs = specs
        self._name_for_file_output = name_for_file_output
        self._exclude_friends = exclude_friends
        self._friends: Optional[List[Player]] = None
        self.set_friends(friends)
    
    def hypixel_object(self) -> hypixel.Player:
        if not self._hypixel_object:
            self._hypixel_object = hypixel.Player(self.uuid())
        return self._hypixel_object

    def uuid(self) -> str:
        return self._uuid_plus_time.uuid()
    
    def time_friended_parent_player(self, format: str) -> Union[str, float, int, None]:
        """format must be 'ms', 's' or 'date' 
        Function will return the time the player friended the parent player. 
        If there is no parent player (e.g., if player is the root player), None is returned."""
        if format == 'ms':
            return self._uuid_plus_time.time_epoch_in_milliseconds()
        elif format == 's':
            return self._uuid_plus_time.time_epoch_in_seconds()
        elif format == 'date':
            return self._uuid_plus_time.date_string()
        else:
            raise ValueError("Invalid value for 'format' parameter.")
    
    def name(self) -> str:
        if not self._name:
            self._name = self.hypixel_object().getName()
        return self._name
    
    def name_for_file_output(self) -> str:
        assert self._name_for_file_output is not None
        return self._name_for_file_output

    def friends(self) -> List[Player]:
        if not self._friends:
            self.set_friends(self.hypixel_object().getFriends())
        return self._friends
    
    def any_specs(self) -> bool:
        return self._specs is not None
    
    def specs(self) -> Specs:
        assert self._specs is not None
        return self._specs
    
    def root_player(self) -> bool:
        return self.specs().root_player()
    
    def friend_of_root_player(self) -> bool:
        return self.specs().friend_of_root_player()
    
    def is_online(self) -> bool:
        return self.hypixel_object().isOnline()
    
    def get_fkdr(self) -> float:
        return self.hypixel_object().getFKDR()
    
    def specs_for_friends(self) -> Optional[Specs]:
        return self.specs().specs_for_friends()
    
    def represents_same_person(self, other: Player) -> bool:
        return self.uuid() == other.uuid()
    
    def set_specs(self, specs: Specs) -> None:
        self._specs = specs
    
    def set_friends(self, friends: Optional[List[Union[UUID_Plus_Time, Player]]]) -> None:
        if not friends:
            self._friends = None
            return
        self._friends = []
        for friend in friends:
            if isinstance(friend, UUID_Plus_Time):
                self._friends.append(Player(friend.uuid(),
                                            time_friended_parent_player=friend.time_epoch_in_seconds()))
            else:
                self._friends.append(friend)
            self._friends[len(self._friends)-1].set_specs(self.specs_for_friends())
    
    def exclude_friends(self) -> bool:
        """Returns whether this player's friends are meant to be excluded, as specified in command line args."""
        assert self._exclude_friends is not None
        return self._exclude_friends
    
    def set_exclude_friends(self, exclude_friends: bool) -> None:
        self._exclude_friends = exclude_friends
    
    def create_dictionary_report(self) -> dict:
        # CONTINUE HERE - later, could make a Report class and return an object of that, instead of a dict here.
        if self.root_player():
            assert not self.time_friended_parent_player('date')
        if self.specs().required_online() and not self.hypixel_object().isOnline():
            return {}

        report = {}
        if self.specs().include_name_fkdr():
            report.update({'name': self.name(), 'fkdr': self.get_fkdr()})
        report['uuid'] = self.uuid()
        if time := self.time_friended_parent_player('ms' if Specs.does_program_display_time_as_unix_epoch() 
                                                    else 'date'):
            report['time'] = time
        if self.specs().print_player_data_exclude_friends():
            print(str(report))
        
        if not self.specs_for_friends():
            return report
        report['friends']: List[dict] = []
        for i, friend in enumerate(self.friends()):
            if self.root_player() and i % 20 == 0:
                print("Processed " + str(i))
            if friend_report := friend.create_dictionary_report():
                report['friends'].append(friend_report)
        return self.polish_dictionary_report(report) if self.root_player() else report
    
    def polish_dictionary_report(self, report: dict) -> dict:
        if 'friends' in report and all('fkdr' in d for d in report['friends']):
            report['friends'] = sorted(report['friends'], key=lambda d: d['fkdr'], reverse=True)
        if self.specs_for_friends() and self.specs_for_friends().required_online():
            report['friends'] = [p for p in report['friends'] if Player(p['uuid']).is_online()]
        if self.specs().print_only_players_friends():
            print('\n\n')
            Utils.print_list_of_dicts(report['friends'])
        return report
    
    def polish_friends_list(self, date_cutoff: Optional[str], friends_to_exclude: List[Player]) -> None:
        if not self._friends:
            return
        self._friends = sorted(self._friends, key=lambda f: f.time_friended_parent_player('s'), reverse=True)
        self._friends = Player.remove_duplicates(self._friends)
        self._friends = [f for f in self._friends if not 
                         any(f.represents_same_person(e) for e in friends_to_exclude)]
        self._friends = Player.remove_players_friended_to_parent_before_date(self._friends, date_cutoff)