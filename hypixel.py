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

HYPIXEL_API_KEY_LENGTH = 36 # This is the length of a Hypixel-API key. Don't change from 36.
verified_api_keys: List[str] = []

requestCache: dict = {}
cacheTime = 60

TIME_STARTED: float = time()
CHOSEN_API_RATE: float = 0.95
num_api_calls_made: int = 0
num_cumulative_calls_at_timestamps = {0.0: 0} # key timestamp (time() - TIME_STARTED), value num api calls made

class PlayerNotFoundException(Exception):
    """ Simple exception if a player/UUID is not found. This exception can usually be ignored.
        You can catch this exception with ``except hypixel.PlayerNotFoundException:`` """
    pass

class HypixelAPIError(Exception):
    """ Simple exception if something's gone very wrong and the program can't continue. """
    pass

def num_cumulative_calls_up_to_timestamp(timestamp_target: float) -> int:
    """Returns the number of api calls made from the start of the program up to the timestamp"""
    if timestamp_target < 0:
        return 0
    for timestamp, num_calls in reversed(num_cumulative_calls_at_timestamps.items()):
        if timestamp < timestamp_target:
            return num_calls
    raise RuntimeError("Nothing returned")

def sleep_for_rate_limiting() -> None:
    if num_api_calls_made < (CHOSEN_API_RATE * 60):
        return
    time_passed = time() - TIME_STARTED
    num_calls_over_last_min = num_api_calls_made - num_cumulative_calls_up_to_timestamp(time_passed - 60)
    if num_calls_over_last_min / 60 < CHOSEN_API_RATE:
        return
    sleep_duration = num_calls_over_last_min / CHOSEN_API_RATE - 60 + 5
    if sleep_duration > 10:
        print("Sleeping " + str(round(sleep_duration, 2)) + " seconds for rate limiting...")
    sleep(sleep_duration)

def getJSON(typeOfRequest, **kwargs):
    global num_api_calls_made
    global num_cumulative_calls_at_timestamps
    """ This private function is used for getting JSON from Hypixel's Public API. """
    num_api_calls_made += 1
    num_cumulative_calls_at_timestamps[time() - TIME_STARTED] = num_api_calls_made
    sleep_for_rate_limiting()
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
            if not Utils.is_uuid(uuid):
                UUIDType = 'name' # TODO: I could probably clean this up somehow.
        if typeOfRequest == 'skyblockplayer':
            typeOfRequest = "/skyblock/profiles"
        for name, value in kwargs.items():
            if typeOfRequest == "player" and name == "uuid":
                name = UUIDType
            requestEnd += '&{}={}'.format(name, value)

    cacheURL = HYPIXEL_API_URL + '{}?key={}{}'.format(typeOfRequest, "None", requestEnd) # TODO: Lowercase
    allURLS = [HYPIXEL_API_URL + '{}?key={}{}'.format(typeOfRequest, api_key, requestEnd)] # Create request URL.
    # Note - the `allURLS` one is already always lowercase, doesn't have 'None' in it. So nothing to do there.

    # If url exists in request cache, and time hasn't expired...
    if cacheURL in requestCache and requestCache[cacheURL]['cacheTime'] > time():
        response = requestCache[cacheURL]['data'] # TODO: Extend cache time
    else:
        requests = (grequests.get(u) for u in allURLS)
        responses = grequests.imap(requests)
        for r in responses:
            response = r.json()

        if not response['success']:
            raise HypixelAPIError(response)
        if typeOfRequest == 'player':
            if response['player'] is None:
                raise PlayerNotFoundException(uuid)
        if typeOfRequest != 'key': # Don't cache key requests.
            requestCache[cacheURL] = {}
            requestCache[cacheURL]['data'] = response
            requestCache[cacheURL]['cacheTime'] = time() + cacheTime # Cache request and clean current cache.
            cleanCache()
    try:
        return response[typeOfRequest]
    except KeyError:
        return response

def get_uuid_from_textfile_if_exists(ign: str) -> str:
    """ - A uuid will be returned if a pair for the ign is found in uuids.txt.
        - If a pair isn't found, the ign itself will just be returned."""
    assert not Utils.is_uuid(ign)
    result = Files.ign_uuid_pairs_in_uuids_txt().get(ign.lower(), ign) # result may be either the ign or a uuid
    if Utils.is_uuid(result) and Player(result).getName().lower() != ign.lower():
        # uuid found for the ign in uuids.txt, but the player has since changed their ign.
        print("NOTE: " + ign + " is no longer the ign of the player with uuid " + result)
        sleep(20) # Since I'd like to know if this ever happens - sleeping isn't necessary for the program itself.
        return ign
    else:
        return result

def cleanCache():
    """ This function is occasionally called to clean the cache of any expired objects. """
    itemsToRemove = []
    for item in requestCache:
        try:
            if requestCache[item]['cacheTime'] < time():
                itemsToRemove.append(item)
        except:
            pass
    for item in itemsToRemove:
        requestCache.pop(item)

def set_api_keys() -> None:
    """ This function is used to set your Hypixel API keys.
        It also checks that they are valid/working.

        Raises
        ------
        HypixelAPIError
            If any of the keys are invalid or don't work, this will be raised.
    """

    api_keys: List[str] = []
    with open('api-key.txt') as file:
        for line in file:
            api_keys.append(line.rstrip())

    for api_key in api_keys:
        if len(api_key) == HYPIXEL_API_KEY_LENGTH:
            response = getJSON('key', key=api_key)
            if response['success']:
                verified_api_keys.append(api_key)
            else:
                raise HypixelAPIError("hypixel/setKeys: Error with key XXXXXXXX-XXXX-XXXX-XXXX{} | {}".format(api_key[23:], response))
        else:
            raise HypixelAPIError("hypixel/setKeys: The key '{}' is not 36 characters.".format(api_key))

class Player:
    """ This class represents a player on Hypixel as a single object.
        A player has a UUID, a username, statistics etc.

        Parameters
        -----------
        Username/UUID : string
            Either the UUID or the username (Deprecated) for a Minecraft player.

        Attributes
        -----------
        JSON : string
            The raw JSON receieved from the Hypixel API.
    """

    def __init__(self, UUID_or_ign: str):
        self.JSON = getJSON('player', uuid=(UUID_or_ign if Utils.is_uuid(UUID_or_ign) 
                                            else get_uuid_from_textfile_if_exists(UUID_or_ign)))

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
    
    def getUUID(self):
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
        if not extra_online_check:
            return False

        # This player doesn't show their online status, but we're not on the first pass through
        # friends. So, we can check if any stats from a few mins ago have been updated.
        currJSON = getJSON('player', uuid=self.getUUID())
        return self.JSON != currJSON
    
    def getFKDR(self) -> float:
        if not self.JSON or 'stats' not in self.JSON or 'Bedwars' not in self.JSON['stats']:
            return 0
        return Utils.fkdr_division(self.JSON['stats']['Bedwars'].get('final_kills_bedwars', 0), 
                                   self.JSON['stats']['Bedwars'].get('final_deaths_bedwars', 0))
    
    def getBedwarsStar(self) -> int:
        if not self.JSON or 'achievements' not in self.JSON or 'bedwars_level' not in self.JSON['achievements']:
            return 0
        return self.JSON['achievements']['bedwars_level']