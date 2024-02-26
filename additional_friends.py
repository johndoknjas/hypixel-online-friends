from typing import List

import Utils
import hypixel
from MyClasses import Specs
import Files
from Player import Player

def get_friends_from_user(friends_specs: Specs) -> List[Player]:
    friends: List[Player] = []
    INPUT_MSG = "Enter the igns/uuids of additional friends, separated by spaces (or enter 'done' to stop): "
    for i, user_input in enumerate(inputs := input(INPUT_MSG).split()):
        if user_input.lower() in ('done', 'stop'):
            assert i == len(inputs)-1
            return friends
        friends.append(Player(hypixel.get_uuid(user_input), specs=friends_specs,
                              time_friended_parent_player=Utils.get_current_date()))
    return friends + get_friends_from_user(friends_specs)

def make_player_with_friends(player_name: str) -> Player:
    """Creates a player with friends, from user input."""
    friends_specs = Specs(False, False, None, 1)
    player = Player(hypixel.get_uuid(player_name), friends=get_friends_from_user(friends_specs),
                    specs=Specs(False, False, friends_specs, 0))
    player.set_name_for_file_output(player.name())
    return player

def add_additional_friends_to_file_system(player_name: str) -> None:
    Specs.set_common_specs(True, False)
    player = make_player_with_friends(player_name)
    file_description = f"Additional friends of {player.name_for_file_output()}, {Utils.get_current_date()}"
    Files.write_data_as_json_to_file(player.create_dictionary_report(), file_description)
