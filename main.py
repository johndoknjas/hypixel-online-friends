import os
import os.path
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import hypixel
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
        playerSubtract = hypixel.Player(ign_uuid_pairs.get(sys.argv[i].lower(), sys.argv[i].lower()))
        friendsExclude = playerSubtract.getUUIDsOfFriends()
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
            data = {"name:": friend.getName(), "UUID": friend.getUUID()}
            print(str(data))
            online_friends.append(data)

    print("\nDone - online friends:\n")
    print("\n".join([str(d) for d in online_friends]))

if __name__ == '__main__':
    main()