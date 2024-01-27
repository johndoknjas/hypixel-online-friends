""" Simple Hypixel-API in Python, by Snuggle | 2017-09-30 to 2018-06-14 
    Modifications made by John (late 2022 to current) """
__version__ = '0.8.0'
# pylint: disable=C0103

from random import choice
from time import time, sleep
import datetime
from typing import List, Optional
import re
import requests

from MyClasses import UUID_Plus_Time
import Files
import Utils
import leveling

HYPIXEL_API_URL = 'https://api.hypixel.net/'

HYPIXEL_API_KEY_LENGTH = 36
verified_api_keys: List[str] = []

TIME_STARTED: float = time()
num_api_calls_made: int = 0

_verify_requests: Optional[bool] = None

class PlayerNotFoundException(Exception):
    """ Simple exception if a player/UUID is not found. This exception can usually be ignored.
        You can catch this exception with ``except hypixel.PlayerNotFoundException:`` """

class HypixelAPIError(Exception):
    """ Simple exception if something's gone very wrong and the program can't continue. """

def getJSON(typeOfRequest: str, uuid_or_ign: str) -> dict:
    """ This function is used for getting a JSON from Hypixel's Public API. """
    global num_api_calls_made
    num_api_calls_made += 1
    # print(str(num_api_calls_made) + '\n' + str(time() - TIME_STARTED) + '\n\n')
    if typeOfRequest != 'player':
        assert Utils.is_uuid(uuid_or_ign)
    assert _verify_requests is not None

    requestEnd = '{}={}'.format('uuid' if Utils.is_uuid(uuid_or_ign) else 'name', uuid_or_ign)
    requestURL = HYPIXEL_API_URL + '{}?{}'.format(typeOfRequest, requestEnd)
    response = requests.get(requestURL, headers={"API-Key": get_api_key()}, verify=_verify_requests)
    try:
        responseHeaders, responseJSON = response.headers, response.json()
    except Exception as e:
        raise Exception(
            f'{response.content}\nresponse content ^\nuuid_or_ign: {uuid_or_ign}\n'
            f'typeOfRequest: {typeOfRequest}\nthere was a problem with response.json()'
        ) from e

    if 'RateLimit-Remaining' in responseHeaders:
        remaining_allowed_requests = int(responseHeaders['RateLimit-Remaining'])
        if remaining_allowed_requests <= 1:
            sleep_seconds = int(responseHeaders['RateLimit-Reset']) + 1
            wake_up_time = datetime.datetime.now() + datetime.timedelta(seconds=sleep_seconds)
            print("Sleeping until " + wake_up_time.strftime("%I:%M:%S %p") + " for rate limiting.")
            sleep(sleep_seconds)

    if not responseJSON['success']:
        raise HypixelAPIError(responseJSON)
    if typeOfRequest == 'player' and responseJSON['player'] is None:
        raise PlayerNotFoundException(uuid_or_ign)
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
    assert not verified_api_keys
    with open('api-key.txt') as file:
        verified_api_keys = [line.rstrip() for line in file]
    assert all(len(api_key) == HYPIXEL_API_KEY_LENGTH for api_key in verified_api_keys)

def get_api_key() -> str:
    """This function returns a random api key from the ones stored in api-key.txt"""
    if not verified_api_keys:
        set_api_keys()
    return choice(verified_api_keys)

def set_verify_requests(b: bool) -> None:
    global _verify_requests
    assert _verify_requests is None
    _verify_requests = b

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
        self.JSON = getJSON('player', get_uuid(uuid_or_ign, call_api_last_resort=False))

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
        """ *Deprecated from Hypixel API*
            This function returns a list of the UUIDs of all the player's friends."""
        friends = []
        for friend in getJSON('friends', self.getUUID())['records']:
            friend_uuid = friend["uuidReceiver"] if friend["uuidReceiver"] != self.getUUID() else friend["uuidSender"]
            friends.append(UUID_Plus_Time(friend_uuid, friend['started']))
        return list(reversed(friends))
    
    def isOnline(self, extra_online_check: bool = False) -> bool:
        """ This function returns a bool representing whether the player is online. """
        if 'lastLogin' in self.JSON:
            return (self.JSON['lastLogin'] > self.JSON['lastLogout'] and
                    getJSON('status', self.getUUID())['session']['online'])
        if extra_online_check:
            # This player doesn't have the online status shown, but we can check if stats from
            # a few mins ago have updated:
            return self.JSON != getJSON('player', self.getUUID())
        return False
    
    def getFKDR(self) -> float:
        return Utils.fkdr_division(
            Utils.nested_get(self.JSON, ['stats', 'Bedwars', 'final_kills_bedwars'], 0, int),
            Utils.nested_get(self.JSON, ['stats', 'Bedwars', 'final_deaths_bedwars'], 0, int)
        )
    
    def getBedwarsStar(self) -> int:
        return Utils.nested_get(self.JSON, ['achievements', 'bedwars_level'], 0, int)
    
    def getPitXP(self) -> int:
        return Utils.nested_get(self.JSON, ['stats', 'Pit', 'profile', 'xp'], 0, int)
    
    def getNetworkXP(self) -> int:
        xp = self.JSON['networkExp']
        assert int(xp) == xp
        return int(xp)
    
    def getExactNWLevel(self) -> float:
        return leveling.getExactLevel(self.getNetworkXP())