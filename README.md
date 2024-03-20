# hypixel-online-friends

This program lets you find all the online friends of a certain player. In hypixel you can do this for your own account with '/f list', but afaik there's not an easy way to do this for accounts that you can't log in to.

Note that hypixel.py and leveling.py are originally from https://github.com/Snuggle/hypixel.py/, with modifications made by myself.

### Main features:

Instructions for running:
- Install the python libraries `requests` and `rich`. To use any of the plot features, install `mplcursors` as well.
  To see differences in player jsons over time, install `deepdiff`.
- Make a textfile called 'api-key.txt', and paste your hypixel api key as the first line.
  - To get this api key, make a developer account with hypixel: https://developer.hypixel.net/
- Basic usage is to run with `python3 main.py *username/uuid*`
  - This will output stats for the specified player, and then output any friends for them.
  - Since the `friends` endpoint of hypixel's API was deprecated, you must manually add any friends for them you want.
    To do this, run `python3 main.py addadditionalfriends *username/uuid*`
- If there's a player you run the program on often, consider making an alias for their uuid:
  - Run `python3 main.py updateuuidaliases *username*`
  - Then when running `python3 main.py *username*`, the program will automatically substitute the username for the uuid.
    This is useful when running the program in quick succession for the same player, since the hypixel api forces a cooldown
    when sending in a username instead of a uuid.
- You can also add an optional argument called 'all', if you'd like to output all friends (not just those currently online).
  - E.g., `python3 main.py *username/uuid* all`

### Developer commands:

Open the root directory of the project in the terminal, and then:
  - `vulture .` will find unused code.
  - `mypy .` will typecheck.
  - `pylint *.py` will review the code for style.
  - `pydeps main.py` will output a dependency graph of the project's modules.
  - `python unused-funcs.py` is a basic script I wrote that attempts to find functions which are never/rarely used.
  - `pytest tests.py` runs a few basic automated tests. Requires installing `pytest`. To run manual tests (output to
    the screen needs to be judged by the tester), run `python tests.py`.