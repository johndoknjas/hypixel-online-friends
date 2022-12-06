import os
import os.path
import sys
from hypixelpy import hypixel
import time

def sleep_for_rate_limiting(seconds):
    if seconds > 15:
        print("Sleeping " + str(round(seconds, 2)) + " seconds for rate limiting...")
    time.sleep(seconds)

def fkdr_division(final_kills, final_deaths):
    return final_kills / final_deaths if final_deaths else final_kills

def how_long_to_sleep(num_api_calls_made, time_passed):
    goal_time_passed = num_api_calls_made / 1.8
    return goal_time_passed - time_passed + 5

def main():
    API_KEYS = []
    with open('api-key.txt') as file:
        for line in file:
            API_KEYS.append(line.rstrip())
    hypixel.setKeys(API_KEYS) # This sets the API keys that are going to be used.

    args = [arg.lower() for arg in sys.argv]
    just_online_friends = 'all' not in args
    args = [arg for arg in args if arg != 'all']

    playerName = args[1]
    ign_uuid_pairs = {} # key ign, value uuid
    if os.path.isfile('uuids.txt'):
        with open('uuids.txt') as file:
            for line in file:
                words = line.rstrip().split()
                ign_uuid_pairs[words[0].lower()] = words[1]
    player = hypixel.Player(ign_uuid_pairs.get(playerName, playerName))
    print("fyi, the uuid of the player you're getting friends of is " + player.getUUID())

    playerFriendsUUIDS = player.getUUIDsOfFriends()
    playerFriendsUUIDS = list(reversed(playerFriendsUUIDS))
    for i in range(2, len(args)):
        friendsExclude = hypixel.Player(ign_uuid_pairs.get(args[i], args[i])).getUUIDsOfFriends()
        playerFriendsUUIDS = [f for f in playerFriendsUUIDS if f not in friendsExclude]

    friends = []
    time_started = time.time()

    for i in range(len(playerFriendsUUIDS)):
        time_passed = time.time() - time_started
        num_api_calls = i*2
        if num_api_calls > 100 and num_api_calls / time_passed > 1.8:
            # Almost at API default rate limit of 120 per min.
            sleep_for_rate_limiting(how_long_to_sleep(num_api_calls, time_passed))
            time_passed = time.time() - time_started
        if i % 10 == 0:
            print("Processed " + str(i))
        friend = hypixel.Player(playerFriendsUUIDS[i])
        if not just_online_friends or friend.isOnline():
            fkdr = (fkdr_division(friend.JSON['stats']['Bedwars']['final_kills_bedwars'], 
                                  friend.JSON['stats']['Bedwars']['final_deaths_bedwars'])
                    if ('final_kills_bedwars' in friend.JSON['stats']['Bedwars'] and
                        'final_deaths_bedwars' in friend.JSON['stats']['Bedwars'])
                    else 0
                   )
            data = {'name': friend.getName(), 'FKDR': fkdr, 'UUID': friend.getUUID()}
            print(str(data))
            friends.append(data)
    
    friends = sorted(friends, key=lambda d: d['FKDR'], reverse=True)
    if just_online_friends:
        updated_friends = []
        sleep_for_rate_limiting(10)
        for i in range(len(friends)):
            if i % 5 == 0 and i > 0:
                sleep_for_rate_limiting(5)
            if hypixel.Player(friends[i]['UUID']).isOnline():
                updated_friends.append(friends[i])
        friends = updated_friends
        print("\nDone - online friends:\n")
    else:
        print("\nDone - all friends:\n")
    print("\n".join([str(d) for d in friends]))

if __name__ == '__main__':
    main()