""" Simple Hypixel-API in Python, by Snuggle | 2017-09-30 to 2018-06-14 """
__version__ = '0.8.0'
# pylint: disable=C0103
# TODO: Add more comments. Explain what's happening!
# TODO: Add API-usage stat-tracking. Like a counter of the number of requests and how many per minute etc.

from random import choice
from time import time, sleep
from copy import deepcopy
from typing import List
import grequests
from MyClasses import UUID_Plus_Time
import Files
import Utils

import leveling
import re

HYPIXEL_API_URL = 'https://api.hypixel.net/'
UUIDResolverAPI = "https://sessionserver.mojang.com/session/minecraft/profile/"

HYPIXEL_API_KEY_LENGTH = 36 # This is the length of a Hypixel-API key. Don't change from 36.
verified_api_keys = []

requestCache = {}
cacheTime = 60

TIME_STARTED: float = time()
CHOSEN_API_RATE: float = 1.8
num_api_calls_made: int = 0
num_cumulative_calls_at_timestamps = {0.0: 0} # key timestamp (time() - TIME_STARTED), value num api calls made

class PlayerNotFoundException(Exception):
    """ Simple exception if a player/UUID is not found. This exception can usually be ignored.
        You can catch this exception with ``except hypixel.PlayerNotFoundException:`` """
    pass
class SkyblockUUIDRequired(Exception):
    """Simple exception to tell the user that in the Skyblock API, UUID's are required and names cannot be used.
    Catch this exception with ``except hypixel.SkyblockUUIDRequired:``"""
    pass
class GuildIDNotValid(Exception):
    """ Simple exception if a Guild is not found using a GuildID. This exception can usually be ignored.
        You can catch this exception with ``except hypixel.GuildIDNotValid:`` """
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
    if num_api_calls_made < 100:
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
    result = Files.ign_uuid_pairs().get(ign.lower(), ign) # result may be either the ign or a uuid
    if Utils.is_uuid(result) and Player(result).getName().lower() != ign.lower():
        # uuid found for the ign in uuids.txt, but the player has since changed their ign.
        print("NOTE: " + ign + " is now the ign of another player.")
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


def setCacheTime(seconds):
    """ This function sets how long the request cache should last, in seconds.

        Parameters
        -----------
        seconds : float
            How long you would like Hypixel-API requests to be cached for.
    """
    try:
        global cacheTime
        cacheTime = float(seconds)
        return "Cache time has been successfully set to {} seconds.".format(cacheTime)
    except ValueError as chainedException:
        raise HypixelAPIError("Invalid cache time \"{}\"".format(seconds)) from chainedException

def set_api_keys() -> None:
    """ This function is used to set your Hypixel API keys.
        It also checks that they are valid/working.

        Raises
        ------
        HypixelAPIError
            If any of the keys are invalid or don't work, this will be raised.
    """

    api_keys = []
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

    def getPlayerInfo(self):
        """ This is a simple function to return a bunch of common data about a player. """
        playerInfo = {}
        playerInfo['uuid'] = self.getUUID()
        playerInfo['displayName'] = Player.getName(self)
        playerInfo['rank'] = Player.getRank(self)
        playerInfo['networkLevel'] = Player.getLevel(self)
        JSONKeys = ['karma', 'firstLogin', 'lastLogin',
                    'mcVersionRp', 'networkExp', 'socialMedia', 'prefix']
        for item in JSONKeys:
            try:
                playerInfo[item] = deepcopy(self.JSON[item])
            except KeyError:
                pass
        return playerInfo

    def getName(self, extra_safety_check=True):
        """ Just return player's name. """
        if not extra_safety_check:
            return self.JSON['displayname']
        sanitized_name = re.sub("[^A-Za-z0-9_]", "", self.JSON['displayname'])
        # Removes any leading whitespace, and only keeps alphanumerics and underscores.
        if self.JSON['displayname'] != sanitized_name:
            raise RuntimeError("Potentially unsafe character in ign - sanitized version is " + sanitized_name
            + ". To disable this safety check, call this function with getName(extra_safety_check=False).")
        return sanitized_name

    def getLevel(self):
        """ This function calls leveling.py to calculate a player's network level. """
        
        networkExp = self.JSON.get('networkExp', 0)        
        networkLevel = self.JSON.get('networkLevel', 0)
        
        exp = leveling.getExperience(networkExp, networkLevel)
        myoutput = leveling.getExactLevel(exp)
        return myoutput
    
    def getUUID(self):
        """ This function returns a player's UUID. """
        return self.JSON['uuid']
        
    def getRank(self):
        """ This function returns a player's rank, from their data. """
        playerRank = {} # Creating dictionary.
        playerRank['wasStaff'] = False
        possibleRankLocations = ['packageRank', 'newPackageRank', 'monthlyPackageRank', 'rank']
        # May need to add support for multiple monthlyPackageRank's in future.

        for Location in possibleRankLocations:
            if Location in self.JSON:
                if Location == 'rank' and self.JSON[Location] == 'NORMAL':
                    playerRank['wasStaff'] = True
                else:
                    if self.JSON[Location] == "NONE": # If monthlyPackageRank expired, ignore "NONE". See: https://github.com/Snuggle/hypixel.py/issues/9
                        continue
                    dirtyRank = self.JSON[Location].upper().replace("_", " ").replace(" Plus", "+")
                    playerRank['rank'] = dirtyRank.replace("Superstar", "MVP++").replace("Youtuber", "YouTube")

        if 'rank' not in playerRank:
            playerRank['rank'] = 'Non'

        return playerRank

    def getGuildID(self):
        """ This function is used to get a GuildID from a player. """
        GuildID = getJSON('findGuild', byUuid=self.getUUID())
        return GuildID['guild']

    def getSession(self):
        """ This function is used to get a player's session information. """
        try:
            session = getJSON('session', uuid=self.getUUID())
        except HypixelAPIError:
            session = None
        return session
    
    def getFriends(self) -> List[UUID_Plus_Time]:
        """ This function returns a list of the UUIDs of all the player's friends."""
        friends = []
        for friend in getJSON('friends', uuid=self.getUUID())['records']:
            friend_uuid = friend["uuidReceiver"] if friend["uuidReceiver"] != self.getUUID() else friend["uuidSender"]
            friends.append(UUID_Plus_Time(friend_uuid, friend['started']))
        return list(reversed(friends))
    
    def isOnline(self):
        """ This function returns a bool representing whether the player is online. """
        onlineStatus = getJSON('status', uuid=self.getUUID())
        return onlineStatus['session']['online']
    
    def getFKDR(self) -> float:
        if not self.JSON or 'stats' not in self.JSON or 'Bedwars' not in self.JSON['stats']:
            return 0
        return Utils.fkdr_division(self.JSON['stats']['Bedwars'].get('final_kills_bedwars', 0), 
                                   self.JSON['stats']['Bedwars'].get('final_deaths_bedwars', 0))
    
    def getBedwarsStar(self) -> int:
        if not self.JSON or 'achievements' not in self.JSON or 'bedwars_level' not in self.JSON['achievements']:
            return 0
        return self.JSON['achievements']['bedwars_level']

class Guild:
    """ This class represents a guild on Hypixel as a single object.
        A guild has a name, members etc.

        Parameters
        -----------
        GuildID : string
            The ID for a Guild. This can be found by using :class:`Player.getGuildID()`.


        Attributes
        -----------
        JSON : string
            The raw JSON receieved from the Hypixel API.

        GuildID : string
            The Guild's GuildID.

    """
    JSON = None
    GuildID = None
    def __init__(self, GuildID):
        try:
            if len(GuildID) == 24:
                self.GuildID = GuildID
                self.JSON = getJSON('guild', id=GuildID)
        except Exception as chainedException:
            raise GuildIDNotValid(GuildID) from chainedException

    def getMembers(self):
        """ This function enumerates all the members in a guild.
        Mojang's API rate-limits this weirdly.
        This is an extremely messy helper function. Use at your own risk. """
        guildRoles = ['MEMBER', 'OFFICER', 'GUILDMASTER'] # Define variables etc.
        memberDict = self.JSON['members']
        allGuildMembers = {}
        for role in guildRoles: # Make allGuildMembers =
            allGuildMembers[role] = [] # {MEMBER: [], OFFICER: [], GUILDMASTER: []}
        allURLS = []
        URLStoRequest = []
        roleOrder = []
        memberList = []
        requests = None
        responses = None
        for member in memberDict: # For each member, use the API to get their username.
            roleOrder.append(member['rank'])
            if UUIDResolverAPI + member['uuid'] in requestCache:
                print("cached")
                allURLS.append(requestCache[UUIDResolverAPI + member['uuid']]['name'])
            else:
                print("NOPE")
                allURLS.append(UUIDResolverAPI + member['uuid'])
                URLStoRequest.append(UUIDResolverAPI + member['uuid'])
        requests = (grequests.get(u) for u in URLStoRequest)
        responses = grequests.map(requests)
        for response in responses:
            requestCache[UUIDResolverAPI + response.json()['id']] = response.json()
        i = 0
        for uindex, user in enumerate(allURLS):
            try:
                if user.startswith(UUIDResolverAPI):
                    allURLS[uindex] = responses[i].json()['name']
                    i += 1
            except AttributeError:
                pass
        i = 0
        for name in allURLS:
            try:
                member = {'role': roleOrder[i], 'name': name}
            except KeyError:
                member = {'role': roleOrder[i], 'name': 'Unknown'}
            memberList.append(member)
            i += 1
        for member in memberList:
            roleList = allGuildMembers[member['role']]
            roleList.append(member['name'])

        return allGuildMembers

class Auction:
    """ This class represents an auction on Hypixel Skyblock as a single object.
    """
    def __init__(self):
        """"Called to create an Auction class."""
        pass    
    def getAuctionInfo(self, PageNumber):
        """Gets all the auction info for a specified page. PageNumber is the page that is requested and can be in int form or string"""
        return getJSON("skyblock/auction", page = str(PageNumber))
    #TODO Add more info

class SkyblockPlayer:
    """A class for a Skyblock player. It requires a UUID, and will return stats on the player
    Raises
    ------
    SkyblockUUIDRequired
        If you pass in a normal username such as RedKaneChironic, will throw an error as Hypixel Skyblock's API currently does not support usernames
    PlayerNotFoundException
        If the player cannot be found, this will be raised.
        
    Parameters
    -----------
    UUID: string
        UUID of the Player
    JSON: string
        Raw JSON data"""
    def __init__(self, UUID):
        self.UUID = UUID
        if len(UUID) <= 16: #UUID is a Minecraft username
            raise SkyblockUUIDRequired(UUID)
        elif len(UUID) in (32, 36):
            self.JSON = getJSON('skyblock/player', uuid = UUID)
        else:
            raise PlayerNotFoundException(UUID)
        
if __name__ == "__main__":
    print("This is a Python library and shouldn't be run directly.\n"
          "Please look at https://github.com/Snuggle/hypixel.py for usage & installation information.")