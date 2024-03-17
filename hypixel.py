""" Simple Hypixel-API in Python, by Snuggle | 2017 to 2021 (https://github.com/Snuggle/hypixel.py/blob/main/hypixel.py)
    Modifications made by John (late 2022 to current) """
__version__ = '0.8.0'
# pylint: disable=C0103

from random import choice
from time import time, sleep
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import re
from dataclasses import dataclass
from copy import deepcopy
import requests

from MyClasses import UUID_Plus_Time
import Files
import Utils
from Args import Args
import leveling
import Colours
from Colours import Hex

def _get_api_keys_from_file() -> List[str]:
    """ This function gets the api key(s) from `api-key.txt`, and returns them in a list. """
    with open('api-key.txt') as file:
        return [line.rstrip() for line in file]

API_KEYS: List[str] = _get_api_keys_from_file()
HYPIXEL_API_URL: str = 'https://api.hypixel.net/'
TIME_STARTED: float = time()
num_api_calls_made: int = 0
_args: Optional[Args] = None

def set_args(args: Args) -> None:
    global _args
    assert not _args
    _args = deepcopy(args)
    if not _args.verify_requests():
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sleep_till: Optional[datetime] = None
def getJSON(typeOfRequest: str, uuid_or_ign: str) -> dict:
    """ This function is used for getting a JSON from Hypixel's Public API. """
    global sleep_till, num_api_calls_made
    assert _args

    if sleep_till and (sleep_duration := (sleep_till - datetime.now()).total_seconds()) >= 0:
        print(f"Sleeping until {sleep_till.strftime('%I:%M:%S %p')} for rate limiting.")
        sleep(sleep_duration)
    sleep_till = None

    num_api_calls_made += 1
    if _args.debug_api():
        print(f"{num_api_calls_made}\n{time() - TIME_STARTED}\n\n")

    if typeOfRequest != 'player':
        assert Utils.is_uuid(uuid_or_ign)
    requestEnd = f"{'uuid' if Utils.is_uuid(uuid_or_ign) else 'name'}={uuid_or_ign}"
    requestURL = f"{HYPIXEL_API_URL}{typeOfRequest}?{requestEnd}"
    response = requests.get(requestURL, headers={"API-Key": choice(API_KEYS)}, verify=_args.verify_requests())
    try:
        responseHeaders, responseJSON = response.headers, response.json()
    except Exception as e:
        raise Exception(
            f'{response.content.decode()}\nresponse content ^\nuuid_or_ign: {uuid_or_ign}\n'
            f'typeOfRequest: {typeOfRequest}\nthere was a problem with response.json()'
        ) from e

    if 'RateLimit-Remaining' in responseHeaders and int(responseHeaders['RateLimit-Remaining']) <= 1:
        sleep_till = datetime.now() + timedelta(seconds=int(responseHeaders['RateLimit-Reset'])+1)

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

    uuid_or_ign = uuid_or_ign.lower()
    if Utils.is_uuid(uuid_or_ign):
        return uuid_or_ign
    ign = uuid_or_ign
    possible_uuid = Files.ign_uuid_pairs_in_uuids_txt().get(ign, ign)
    if Utils.is_uuid(possible_uuid):
        if Player(possible_uuid).getName().lower() != ign:
            raise RuntimeError(f"NOTE: {ign} is no longer the ign of the player with uuid {possible_uuid}")
        return possible_uuid
    return Player(ign).getUUID() if call_api_last_resort else ign

class PlayerNotFoundException(Exception):
    """ Simple exception if a player/UUID is not found. This exception can usually be ignored.
        You can catch this exception with ``except hypixel.PlayerNotFoundException:`` """

class HypixelAPIError(Exception):
    """ Simple exception if something's gone very wrong and the program can't continue. """

@dataclass
class RankColours:
    plus_colour: Optional[Colours.Hex]
    """Represents the colour of any '+' chars that may be present in the rank."""
    player_name_brackets_colour: Optional[Colours.Hex]
    """Represents the colour of the rank brackets and the player's name."""
    rank_colour: Optional[Colours.Hex]
    """Represents the colour of the rank, excluding any potential '+' chars."""

class RankMap:
    _rank_map: Dict[Optional[str], Tuple[str, RankColours]] = {
        '§c[OWNER]': ('OWNER', RankColours(None, Hex.RED, Hex.RED)),
        'ADMIN': ('ADMIN', RankColours(None, Hex.RED, Hex.RED)),
        'GAME_MASTER': ('GM', RankColours(None, Hex.DARK_GREEN, Hex.DARK_GREEN)),
        'YOUTUBER': ('YOUTUBE', RankColours(None, Hex.RED, Hex.WHITE)),
        'VIP': ('VIP', RankColours(None, Hex.GREEN, Hex.GREEN)),
        'VIP_PLUS': ('VIP+', RankColours(Hex.GOLD, Hex.GREEN, Hex.GREEN)),
        'MVP': ('MVP', RankColours(None, Hex.AQUA, Hex.AQUA)),
        'MVP_PLUS': ('MVP+', RankColours(Hex.UNKNOWN, Hex.AQUA, Hex.AQUA)),
        'SUPERSTAR': ('MVP++', RankColours(Hex.UNKNOWN, Hex.UNKNOWN, Hex.UNKNOWN)),
        None: ('', RankColours(None, None, None))
    }
    @classmethod
    def json_rank_info(cls, key: Optional[str]) -> Tuple[str, RankColours]:
        """Returns the display string for a rank (without the brackets), as well as a RankColours
           object detailing the colours to print in."""
        return deepcopy(cls._rank_map[key])

class Rank:
    def __init__(self, json: dict) -> None:
        keys = ('prefix', 'rank', 'monthlyPackageRank', 'newPackageRank', 'packageRank')
        none_vals = (None, 'NONE', 'NORMAL')
        rank_map_key = next(
            (v for v in (json.get(k) for k in keys) if v not in none_vals), None
        )
        self._display_rank, self._colours = RankMap.json_rank_info(rank_map_key)
        self._json = json

    def rank(self, with_brackets_and_space: bool) -> str:
        """Returns the rank that's displayed ('VIP', 'MVP+', '', etc)"""
        if not with_brackets_and_space or self._display_rank == '':
            return self._display_rank
        return f"[{self._display_rank}] "

    def rank_colour(self) -> Optional[Hex]:
        if self._colours.rank_colour == Hex.UNKNOWN:
            assert self._display_rank == 'MVP++'
            self._colours.rank_colour = (
                Hex.AQUA if self._json.get('monthlyRankColor') == 'AQUA' else Hex.GOLD
            )
        return self._colours.rank_colour

    def plus_colour(self) -> Optional[Hex]:
        if self._colours.plus_colour == Hex.UNKNOWN:
            assert self._display_rank in ('MVP+', 'MVP++')
            json_plus_colour = self._json.get('rankPlusColor')
            self._colours.plus_colour = (Hex.RED if json_plus_colour is None else
                                         next(c for c in Hex if json_plus_colour == c.name))
        return self._colours.plus_colour

    def name_and_bracket_colour(self) -> Optional[Hex]:
        if self._colours.player_name_brackets_colour == Hex.UNKNOWN:
            self._colours.player_name_brackets_colour = self.rank_colour()
        return self._colours.player_name_brackets_colour

    def print_rank(self) -> None:
        from Colours import ColourSpecs, colour_print
        rank = self.rank(False)
        bracket_colour = self.name_and_bracket_colour()
        rank_colour = self.rank_colour()
        if rank == '':
            return
        assert bracket_colour is not None and rank_colour is not None

        colour_print(ColourSpecs('[', bracket_colour))
        colour_print(ColourSpecs(rank.rstrip('+'), rank_colour))
        if '+' in rank:
            assert rank.count('+') <= 2
            assert (plus_colour := self.plus_colour()) is not None
            colour_print(ColourSpecs('+', plus_colour))
            if rank.count('+') == 2:
                colour_print(ColourSpecs('+', plus_colour))
        colour_print(ColourSpecs('] ', bracket_colour))

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
        self.JSON = getJSON('player', get_uuid(uuid_or_ign, call_api_last_resort=False))
        self._rank = Rank(self.JSON)
        self.updated_json: Optional[Tuple[dict, datetime]] = None
        """Stores the newest result of `getJSON('player')` that was updated from the previous call."""

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

    def isOnline(self, extra_online_checks: Tuple[bool, bool]) -> bool:
        """ This function returns a bool representing whether the player is online.
            For `extra_online_checks`:
                - The first bool is for players whose online status is shown. It determines whether to check
                  the current online statuses of players, irrespective of whether they were recorded as
                  online in the original self.JSON. So, this bool being true limits false negatives, at
                  the expense of more api calls.
                - The second bool determines whether to call the api for the most recent json to see if
                  it's changed, for players whose online status is disabled."""
        if {'lastLogin', 'lastLogout'} <= self.JSON.keys():
            return (    (extra_online_checks[0] or self.JSON['lastLogin'] > self.JSON['lastLogout'])
                    and getJSON('status', self.getUUID())['session']['online'])
        # This player doesn't have the online status shown, but we can check if stats from
        # the original self.JSON have updated (if the caller has enabled this feature):
        if extra_online_checks[1] and self.JSON != (json := getJSON('player', self.getUUID())):
            self.set_updated_json_if_applicable(json)
            return True
        return False

    def set_updated_json_if_applicable(self, new_json: dict) -> None:
        assert _args
        if new_json == (curr_latest_json := self.updated_json[0] if self.updated_json else self.JSON):
            return
        if _args.show_json_updates():
            Utils.print_diff_dicts(curr_latest_json, new_json, f"\nUpdates to json for {self.getName()}: ")
        self.updated_json = (new_json, datetime.now())

    def getFKDR(self) -> float:
        return Utils.kdr_division(
            Utils.nested_get(self.JSON, ('stats', 'Bedwars', 'final_kills_bedwars'), 0, int),
            Utils.nested_get(self.JSON, ('stats', 'Bedwars', 'final_deaths_bedwars'), 0, int)
        )

    def getBedwarsStar(self) -> int:
        return Utils.nested_get(self.JSON, ('achievements', 'bedwars_level'), 0, int)

    def getBedwarsXP(self) -> int:
        xp = Utils.nested_get(self.JSON, ('stats', 'Bedwars', 'Experience'), 0)
        assert int(xp) == xp
        return int(xp)

    def getPitXP(self) -> int:
        return Utils.nested_get(self.JSON, ('stats', 'Pit', 'profile', 'xp'), 0, int)

    def getPitPlaytime(self) -> int:
        """Returns the total pit playtime in minutes."""
        return Utils.nested_get(self.JSON, ('stats', 'Pit', 'pit_stats_ptl', 'playtime_minutes'), 0, int)

    def getPitKills(self) -> int:
        return Utils.nested_get(self.JSON, ('stats', 'Pit', 'pit_stats_ptl', 'kills'), 0, int)

    def getPitDeaths(self) -> int:
        return Utils.nested_get(self.JSON, ('stats', 'Pit', 'pit_stats_ptl', 'deaths'), 0, int)

    def getNetworkXP(self) -> int:
        xp = self.JSON['networkExp']
        assert int(xp) == xp
        return int(xp)

    def getExactNWLevel(self) -> float:
        return leveling.getExactLevel(self.getNetworkXP())

    def getNetworkRank(self) -> Rank:
        return self._rank
