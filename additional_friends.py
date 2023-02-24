from typing import Optional, List

import Utils
import hypixel
from MyClasses import Specs
import Files
from Player import Player

def get_uuid(uuid_or_ign: str) -> Optional[str]:
    """If the param is a uuid, it just gets returned. Otherwise if it's an ign, the associated uuid
       will be returned. If a uuid cannot be found for it, None will be returned."""
    if Utils.is_uuid(uuid_or_ign):
        return uuid_or_ign
    uuid_or_ign = hypixel.get_uuid_from_textfile_if_exists(uuid_or_ign)
    if Utils.is_uuid(uuid_or_ign):
        return uuid_or_ign
    try:
        player = hypixel.Player(uuid_or_ign)
    except:
        return None
    else:
        return player.getUUID()

def make_player_with_friends(player_name: str, get_from_file_system: bool) -> Player:
    """Creates a player with friends, either from user input, or from getting all additional friends
       stored in the file system."""
    friends_specs = Specs(False, False, None, 1)
    player_specs = Specs(False, False, friends_specs, 0)
    friends: List[Player] = []
    if get_from_file_system:
        pass
        # CONTINUE HERE - get additional friends from file system, add to the 'friends' var.
        # Then, these friends will be added to the player object returned at the end of this function.
        # In this scenario, the caller of this function will probably be from main, such as in
        # get_players_from_args(). Note that before calling this function, you'd have to check
        # if any files starting with "Additional friends..." exist in the file system for the given player.
    else:
        user_input = input("Enter the ign/uuid of an additional friend (or 'done' to stop): ")
        while user_input != 'done':
            current_friend_uuid = get_uuid(user_input)
            if not current_friend_uuid:
                user_input = input("Nothing found for that ign - please enter the uuid instead: ")
            else:
                friends.append(Player(current_friend_uuid, specs=friends_specs))
                user_input = input("Enter the ign/uuid of an additional friend (or 'done' to stop): ")
    player = Player(get_uuid(player_name), friends=friends, specs=player_specs)
    player.set_name_for_file_output(player.name())
    return player

def add_additional_friends_to_file_system(player_name: str) -> None:
    Specs.set_common_specs(True, False)
    player = make_player_with_friends(player_name, False)
    file_description = ("Additional friends of " + player.name_for_file_output() + ", " + Utils.get_current_date())
    Files.write_data_as_json_to_file(player.create_dictionary_report(), file_description)
