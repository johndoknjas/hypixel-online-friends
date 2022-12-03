# hypixel-online-friends

This program lets you find all the online friends of a certain player. In hypixel you can do this for your own account with '/f list', but afaik there's not an easy way to do this for accounts that you can't log in to.

Note that hypixel.py and leveling.py are from https://github.com/Snuggle/hypixel.py/, with a few small modifications added by myself to the former file.

Instructions for running:
- Do pip3 install grequests
- Make a textfile called 'api-key.txt', and paste your hypixel api key as the first line.
  - To get this api key, log in on hypixel's server and do the command '/api'
- Run with python3 main.py "username"
  - Where 'username' is a command line argument representing the user for whom you want to find all friends curerently online.
  - E.g., python3 main.py ItsTreasonThen will output all online friends of ItsTreasonThen.
- You can also run with more command line arguments. E.g.:
  - python3 main.py ItsTreasonThen TreasonsSon will output all online friends who are friends of ItsTreasonThen, but not TreasonsSon.
- If you know the UUIDs of any players in your command line arguments, make a textfile called 'uuids.txt', and on each line write the player's username, followed by a space, followed by their UUID.
  - This isn't required, but it may be helpful with calling the hypixel api if you'll be running this script multiple times in a short window.
