""" Simple Hypixel-API in Python, by Snuggle | 2017-09-30 to 2018-06-14 
    Modifications made by John (late 2022 to current) """
__version__ = '0.8.0'
# pylint: disable=C0103

from random import choice
from time import time, sleep
from typing import List
import re
import grequests # type: ignore

from MyClasses import UUID_Plus_Time
import Files
import Utils

HYPIXEL_API_URL = 'https://api.hypixel.net/'

HYPIXEL_API_KEY_LENGTH = 36
verified_api_keys: List[str] = []

TIME_STARTED: float = time()
num_api_calls_made: int = 0

class PlayerNotFoundException(Exception):
    """ Simple exception if a player/UUID is not found. This exception can usually be ignored.
        You can catch this exception with ``except hypixel.PlayerNotFoundException:`` """
    pass

class HypixelAPIError(Exception):
    """ Simple exception if something's gone very wrong and the program can't continue. """
    pass

def getJSON(typeOfRequest, **kwargs) -> dict:
    """ This function is used for getting a JSON from Hypixel's Public API. """
    global num_api_calls_made

    num_api_calls_made += 1
    # print(str(num_api_calls_made) + '\n' + str(time() - TIME_STARTED) + '\n\n')

    requestEnd = ''
    if typeOfRequest == 'key':
        api_key = kwargs['key']
    else:
        if not verified_api_keys:
            set_api_keys()
        api_key = choice(verified_api_keys) # Select a random API key from the list available.

        if typeOfRequest == 'player':
            UUIDType = 'uuid'
            uuid = kwargs['uuid']
            if Utils.is_ign(uuid):
                UUIDType = 'name' # TODO: I could probably clean this up somehow.
        if typeOfRequest == 'skyblockplayer':
            typeOfRequest = "/skyblock/profiles"
        conjunct_in_url = ''
        for name, value in kwargs.items():
            if typeOfRequest == "player" and name == "uuid":
                name = UUIDType
            requestEnd += (conjunct_in_url + '{}={}'.format(name, value))
            conjunct_in_url = '&'

    custom_headers = {"API-Key": api_key}
    allURLS = [HYPIXEL_API_URL + '{}?{}'.format(typeOfRequest, requestEnd)] # Create request URL.
    requests = (grequests.get(u, headers=custom_headers) for u in allURLS)
    response = next(grequests.imap(requests))
    responseHeaders, responseJSON = response.headers, response.json()

    if 'RateLimit-Remaining' in responseHeaders:
        remaining_allowed_requests = int(responseHeaders['RateLimit-Remaining'])
        if remaining_allowed_requests <= 1:
            sleep(int(responseHeaders['RateLimit-Reset']) + 1)

    if not responseJSON['success']:
        raise HypixelAPIError(responseJSON)
    if typeOfRequest == 'player' and responseJSON['player'] is None:
        raise PlayerNotFoundException(uuid)
    try:
        return responseJSON[typeOfRequest]
    except KeyError:
        return responseJSON
    
def get_uuid(uuid_or_ign: str, call_api_last_resort: bool = True) -> str:
    """Param can be an ign or uuid. If it's a uuid, this function will return it immediately. Otherwise,
       it will try to get it from uuids.txt (and if so, then verify the player's current ign is still the same
       by using a temp hypixel object). Finally if this fails, a temp hypixel object is created in order to call
       getUUID() - unless `call_api_last_resort` is False, in which case the ign is just returned."""
    
    assert uuid_or_ign == uuid_or_ign.lower()
    if Utils.is_uuid(uuid_or_ign):
        return uuid_or_ign
    ign = uuid_or_ign
    possible_uuid = Files.ign_uuid_pairs_in_uuids_txt().get(ign, ign)
    if Utils.is_uuid(possible_uuid):
        if Player(possible_uuid).getName().lower() != ign:
            raise RuntimeError("NOTE: " + ign + " is no longer the ign of the player with uuid " + possible_uuid)
        return possible_uuid
    return Player(ign).getUUID() if call_api_last_resort else ign

def set_api_keys() -> None:
    """ This function gets the api key(s) from `api-key.txt` and stores them in `verified_api_keys`. The
        function also checks that the api keys are all of the required length.
    """
    global verified_api_keys
    with open('api-key.txt') as file:
        verified_api_keys = [line.rstrip() for line in file]
    assert all(len(api_key) == HYPIXEL_API_KEY_LENGTH for api_key in verified_api_keys)

class Player:
    """ This class represents a player on Hypixel as a single object.
        A player has a UUID, a username, statistics etc.

        Parameters
        -----------
        Username/UUID : string
            Either the UUID or the username for a player.

        Attributes
        -----------
        JSON : string
            The raw JSON receieved from the Hypixel API.
    """

    def __init__(self, uuid_or_ign: str) -> None:
        # print(uuid_or_ign)
        self.JSON = getJSON('player', uuid=get_uuid(uuid_or_ign, call_api_last_resort=False))

    def getName(self, extra_safety_check=True) -> str:
        """ Just return player's name. """
        if not extra_safety_check:
            return self.JSON['displayname']
        sanitized_name = re.sub("[^A-Za-z0-9_]", "", self.JSON['displayname'])
        # Removes any leading whitespace, and only keeps alphanumerics and underscores.
        if self.JSON['displayname'] != sanitized_name:
            raise RuntimeError("Potentially unsafe character in ign - sanitized version is " + sanitized_name
            + ". To disable this safety check, call this function with getName(extra_safety_check=False).")
        return sanitized_name
    
    def getUUID(self) -> str:
        """ This function returns a player's UUID. """
        return self.JSON['uuid']
    
    def getFriends(self) -> List[UUID_Plus_Time]:
        """ This function returns a list of the UUIDs of all the player's friends."""
        friends = []
        for friend in getJSON('friends', uuid=self.getUUID())['records']:
            friend_uuid = friend["uuidReceiver"] if friend["uuidReceiver"] != self.getUUID() else friend["uuidSender"]
            friends.append(UUID_Plus_Time(friend_uuid, friend['started']))
        return list(reversed(friends))
    
    def isOnline(self, extra_online_check: bool = False) -> bool:
        """ This function returns a bool representing whether the player is online. """
        if 'lastLogin' in self.JSON:
            return (self.JSON['lastLogin'] > self.JSON['lastLogout'] and
                    getJSON('status', uuid=self.getUUID())['session']['online'])
        if extra_online_check:
            # This player doesn't have the online status shown, but we can check if stats from
            # a few mins ago have updated:
            return self.JSON != getJSON('player', uuid=self.getUUID())
        return False
    
    def getFKDR(self) -> float:
        if not self.JSON or 'stats' not in self.JSON or 'Bedwars' not in self.JSON['stats']:
            return 0
        return Utils.fkdr_division(self.JSON['stats']['Bedwars'].get('final_kills_bedwars', 0), 
                                   self.JSON['stats']['Bedwars'].get('final_deaths_bedwars', 0))
    
    def getBedwarsStar(self) -> int:
        if not self.JSON or 'achievements' not in self.JSON or 'bedwars_level' not in self.JSON['achievements']:
            return 0
        return self.JSON['achievements']['bedwars_level']
    
    def getPitXP(self) -> int:
        if (not self.JSON or 'stats' not in self.JSON or 'Pit' not in self.JSON['stats'] or
            'profile' not in self.JSON['stats']['Pit']):
            return 0
        return self.JSON['stats']['Pit']['profile'].get('xp', 0)