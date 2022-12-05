import os
import os.path
import sys
from hypixelpy import hypixel
import time

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
        while num_api_calls > 100 and num_api_calls / time_passed > 1.8:
            # Almost at API default rate limit of 120 per min.
            print("sleeping 5 seconds for rate limiting...")
            time.sleep(5)
            time_passed = time.time() - time_started
        if i % 10 == 0:
            print("Processed " + str(i))
        friend = hypixel.Player(playerFriendsUUIDS[i])
        if not just_online_friends or friend.isOnline():
            fkdr = (friend.JSON['stats']['Bedwars']['final_kills_bedwars'] / 
                    friend.JSON['stats']['Bedwars']['final_deaths_bedwars'])
            data = {'name': friend.getName(), 'FKDR': fkdr, 'UUID': friend.getUUID()}
            print(str(data))
            friends.append(data)
    
    friends = sorted(friends, key=lambda d: d['FKDR'], reverse=True)
    if just_online_friends:
        print("sleeping " + str(len(friends)) + " seconds for rate limiting...")
        time.sleep(len(friends)) # Rate limiting, as about to do two API calls per element in list.
        friends = [d for d in friends if hypixel.Player(d['UUID']).isOnline()]
        print("\nDone - online friends:\n")
    else:
        print("\nDone - all friends:\n")
    print("\n".join([str(d) for d in friends]))

if __name__ == '__main__':
    main()