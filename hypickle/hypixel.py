from __future__ import annotations

""" Simple Hypixel-API in Python, by Snuggle | 2017 to 2021 (https://github.com/Snuggle/hypixel.py/blob/main/hypixel.py)
    Modifications made by John (late 2022 to current) """
__version__ = '0.8.0'
# pylint: disable=C0103

from random import choice
from time import time, sleep
from datetime import datetime, timedelta
from typing import Optional
import re
import os.path
import requests

from .MyClasses import UUID_Plus_Time, args
from . import Files
from . import Utils
from . import leveling
from .Rank import Rank

TIME_STARTED: float = time()
num_api_calls_made: int = 0

def make_request_url(typeOfRequest: str, uuid_or_ign: str | None) -> str:
    assert (typeOfRequest == 'leaderboards') == (uuid_or_ign is None)
    requestURL = 'https://api.hypixel.net/' + typeOfRequest
    if uuid_or_ign is not None:
        if (query_param_name := 'uuid' if Utils.is_uuid(uuid_or_ign) else 'name') == 'name':
            assert typeOfRequest == 'player'
        requestURL += f"?{query_param_name}={uuid_or_ign}"
    return requestURL

sleep_till: Optional[datetime] = None
def getJSON(typeOfRequest: str, uuid_or_ign: Optional[str], specific_api_key: Optional[str] = None) -> dict:
    """ This function is used for getting a JSON from Hypixel's Public API. """
    global sleep_till, num_api_calls_made

    if sleep_till and (sleep_duration := (sleep_till - datetime.now()).total_seconds()) >= 0:
        print(f"Sleeping until {sleep_till.strftime('%I:%M:%S %p')} for rate limiting.")
        sleep(sleep_duration)
    sleep_till = None

    num_api_calls_made += 1
    if args().debug_api():
        print(f"{num_api_calls_made}\n{time() - TIME_STARTED}\n\n")

    response = requests.get(
        make_request_url(typeOfRequest, uuid_or_ign), verify=args().verify_requests(),
        headers={"API-Key": _get_api_key() if specific_api_key is None else specific_api_key}
    )
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

def _get_api_key() -> str:
    """ This function returns one of the key(s) in `api-key.txt`. If the file doesn't exist, it will ask the
        user for an api key and write it to the new file. """
    FILENAME = 'api-key.txt'
    if not os.path.isfile(FILENAME) or not Utils.content_in_file(FILENAME):
        print("The script needs a hypixel api key. To get one, you can follow the first part of this guide: https://gist.github.com/camnwalter/c0156c68b1e2a21ec0b084c6f04b63f0#how-to-get-a-new-api-key-after-the-hypixel-api-changes")
        while not _validate_api_key(api_key := input("Please enter your api key: ").strip()):
            print('Sorry, that api key is invalid.')
        with open(FILENAME, 'w') as file:
            file.write(api_key)
    with open(FILENAME) as file:
        return choice([x for line in file if (x := line.strip())])

def _validate_api_key(key: str) -> bool:
    try:
        getJSON('leaderboards', None, specific_api_key=key)
    except HypixelAPIError as e:
        if "'cause': 'Invalid API key'" in repr(e):
            return False
        raise RuntimeError('Unexpected error') from e
    return True

def get_uuid(uuid_or_ign: str, call_api_last_resort: bool = True) -> str:
    """Param can be an ign or uuid. If it's a uuid, this function will return it immediately. Otherwise,
       it will try to get it from uuids.txt (and if so, then verify the player's current ign is still the same
       by using a temp hypixel object). Finally if this fails, a temp hypixel object is created in order to call
       getUUID() - unless `call_api_last_resort` is False, in which case the ign is just returned."""

    uuid_or_ign = uuid_or_ign.lower()
    if Utils.is_uuid(uuid_or_ign):
        return uuid_or_ign
    ign = uuid_or_ign
    possible_uuid = Files.ign_uuid_pairs_in_uuids_txt().get(ign,
                    Files.ign_uuid_pairs_in_hypickle_cache().get(ign, ign))
    if Utils.is_uuid(possible_uuid):
        if Player(possible_uuid).getName().lower() != ign:
            raise RuntimeError(f"NOTE: {ign} is no longer the ign of the player with uuid {possible_uuid}")
        return possible_uuid
    return Player(ign).getUUID() if call_api_last_resort else ign

class PlayerNotFoundException(Exception):
    pass

class HypixelAPIError(Exception):
    pass

class Player:
    def __init__(self, uuid_or_ign: str) -> None:
        self.JSON = getJSON('player', get_uuid(uuid_or_ign, call_api_last_resort=False))
        self._rank = Rank(self.JSON)
        self.updated_json: Optional[tuple[dict, datetime]] = None
        """Stores the newest result of `getJSON('player')` that was updated from the previous call."""
        self.recent_games_visible: Optional[bool] = None
        """Recent games may not be visible if the player has turned off the api setting, or if they haven't
           played a game in roughly 3 days it seems."""
        if Utils.is_ign(uuid_or_ign):
            # An ign was passed in, which means storing the uuid in the cache might help save
            # an api call in the near future:
            Files.write_to_file(f"{self.getName().lower()} {self.getUUID()}",
                                "ign_uuid_pair", Files.HYPICKLE_CACHE_FOLDER)

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

    def getFriends(self) -> list[UUID_Plus_Time]:
        """ *Deprecated from Hypixel API*
            This function returns a list of the UUIDs of all the player's friends."""
        friends = []
        for friend in getJSON('friends', self.getUUID())['records']:
            friend_uuid = friend["uuidReceiver"] if friend["uuidReceiver"] != self.getUUID() else friend["uuidSender"]
            friends.append(UUID_Plus_Time(friend_uuid, friend['started']))
        return list(reversed(friends))

    def isOnline(self, extra_online_checks: tuple[bool, bool, bool]) -> bool:
        """ This function returns a bool representing whether the player is online.
            For `extra_online_checks`:
                - The first bool is for players whose online status is shown. It determines whether to check
                  the current online statuses of players, irrespective of whether they were recorded as
                  online in the original self.JSON. So, this bool being true limits false negatives, at
                  the expense of more api calls.
                - The second bool determines whether to call the api for the most recent json to see if
                  it's changed, for players whose online status is disabled.
                - The third bool determines whether, as a last resort, to call the `recentgames` endpoint,
                  in order to see if the most recent game is visible, and if it doesn't have an
                  'ended' key; if so, the player is online."""
        if {'lastLogin', 'lastLogout'} <= self.JSON.keys():
            return (    (extra_online_checks[0] or self.JSON['lastLogin'] > self.JSON['lastLogout'])
                    and getJSON('status', self.getUUID())['session']['online'])
        # This player doesn't have the online status shown, but we can check if stats from
        # the original self.JSON have updated (if the caller has enabled this feature):
        if extra_online_checks[1] and self.JSON != (json := getJSON('player', self.getUUID())):
            self.set_updated_json_if_applicable(json)
            return True
        return extra_online_checks[2] and bool(games := self.getRecentGames()) and 'ended' not in games[0]

    def set_updated_json_if_applicable(self, new_json: dict) -> None:
        if new_json == (curr_latest_json := self.updated_json[0] if self.updated_json else self.JSON):
            return
        if args().show_json_updates():
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

    def getRecentGames(self) -> list[dict]:
        if self.recent_games_visible is False:
            return []
        self.recent_games_visible = bool(recent_games := getJSON('recentgames', self.getUUID())['games'])
        return recent_games
