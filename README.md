# hypickle

A script that outputs realtime stats for custom lists of friends you create.

### Installation:

To install, run the following command:

`pip install hypickle`

Besides installing the script, this will also automatically install its dependencies (the libraries `requests`,
`rich`, `mplcursors`, `deepdiff`, and any of their own dependencies).

Then, create a new folder that will be used to store persistent information (such as friends lists you create).
In this folder, make a textfile called 'api-key.txt', and paste your hypixel api key as the first line.
  - To get this api key, make a [hypixel developer account](https://developer.hypixel.net/).
    The first part of [this](https://gist.github.com/camnwalter/c0156c68b1e2a21ec0b084c6f04b63f0#how-to-get-a-new-api-key-after-the-hypixel-api-changes)
    guide is helpful to do this.

After setting this up, you will be able to open a terminal window in this directory and run various commands
with the `hypickle` script (explained below).

### Main features:

- Basic usage is to run with `hypickle *username/uuid*`
  - This will output stats for the specified player, and then output any friends for them.
  - Since the `friends` endpoint of hypixel's API was deprecated, you must manually add any friends for them you want.
    To do this, run `hypickle addfriends *username/uuid*`
- If there's a player you run the program on often, consider making an alias for their uuid:
  - Run `hypickle updateuuidaliases *username*`
  - Then when running `hypickle *username*`, the program will automatically substitute the username for the uuid.
    This is useful when running the program in quick succession for the same player, since the hypixel api forces a cooldown
    when sending in a username instead of a uuid.
- You can also add an optional argument called 'all', if you'd like to output all friends (not just those currently online).
  - E.g., `hypickle *username/uuid* all`

### Developer commands:

Open the root directory of the project in the terminal, and then:
  - `python3 main.py *args*` allows you to test any local changes you've made to the project.
  - `vulture .` will find unused code.
  - `mypy .` will typecheck.
  - `pylint *.py` will review the code for style.
  - `pydeps hypickle` will output a dependency graph of the project's modules.
  - `python unused-funcs.py` is a basic script I wrote that attempts to find functions which are never/rarely used.
  - `pytest tests.py` runs a few basic automated tests. Requires installing `pytest`. To run manual tests (output to
    the screen needs to be judged by the tester), run `python tests.py`.

### Acknowledgements:

The `hypixel.py` and `leveling.py` files were originally from [Snuggle's repo](https://github.com/Snuggle/hypixel.py/). Since then I have made a number of modifications to them.