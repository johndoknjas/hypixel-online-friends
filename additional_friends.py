from typing import List

import Utils
import hypixel
from MyClasses import Specs
import Files
from Player import Player

def make_player_with_friends(player_name: str) -> Player:
    """Creates a player with friends, from user input."""
    player_uuid = hypixel.get_uuid(player_name)
    friends_specs = Specs(False, False, None, 1)
    player_specs = Specs(False, False, friends_specs, 0)
    friends: List[Player] = []
    user_input = input("Enter the ign/uuid of an additional friend (or 'done' to stop): ")
    while user_input not in ('done', 'stop'):
        current_friend_uuid = hypixel.get_uuid(user_input)
        if not current_friend_uuid:
            user_input = input("Nothing found for that ign - please enter the uuid instead: ")
        else:
            friends.append(Player(current_friend_uuid, specs=friends_specs,
                                  time_friended_parent_player=Utils.get_current_date()))
            user_input = input("Enter the ign/uuid of an additional friend (or 'done' to stop): ")
    player = Player(player_uuid, friends=friends, specs=player_specs)
    player.set_name_for_file_output(player.name())
    return player

def add_additional_friends_to_file_system(player_name: str) -> None:
    Specs.set_common_specs(True, False)
    player = make_player_with_friends(player_name)
    file_description = ("Additional friends of " + player.name_for_file_output() + ", " + Utils.get_current_date())
    Files.write_data_as_json_to_file(player.create_dictionary_report(), file_description)
