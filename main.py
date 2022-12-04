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

    playerName = sys.argv[1].lower()
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
    for i in range(2, len(sys.argv)):
        friendsExclude = hypixel.Player(ign_uuid_pairs.get(sys.argv[i].lower(), sys.argv[i].lower())).getUUIDsOfFriends()
        playerFriendsUUIDS = [f for f in playerFriendsUUIDS if f not in friendsExclude]

    online_friends = []
    print("Figuring out which friends are online:")
    time_started = time.time()

    for i in range(len(playerFriendsUUIDS)):
        time_passed = time.time() - time_started
        num_api_calls = i*2
        while num_api_calls > 100 and num_api_calls / time_passed > 1.8:
            # Almost at API default rate limit of 120 per min.
            time.sleep(5)
            time_passed = time.time() - time_started
        if i % 10 == 0:
            print("Processed " + str(i))
        friend = hypixel.Player(playerFriendsUUIDS[i])
        if friend.isOnline():
            fkdr = (friend.JSON['stats']['Bedwars']['final_kills_bedwars'] / 
                    friend.JSON['stats']['Bedwars']['final_deaths_bedwars'])
            data = {'name': friend.getName(), 'FKDR': fkdr, 'UUID': friend.getUUID()}
            print(str(data))
            online_friends.append(data)
    
    online_friends = sorted(online_friends, key=lambda d: d['FKDR'], reverse=True)
    online_friends = [d for d in online_friends if hypixel.Player(d['UUID']).isOnline()]
    print("\nDone - online friends:\n")
    print("\n".join([str(d) for d in online_friends]))

if __name__ == '__main__':
    main()