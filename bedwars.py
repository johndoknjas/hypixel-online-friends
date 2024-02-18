# Based off https://github.com/Plancke/hypixel-php/blob/master/src/util/games/bedwars/ExpCalculator.php

from math import floor

LEVELS_PER_PRESTIGE = 100
XP_PER_EASY_LEVEL = [500, 1000, 2000, 3500]
XP_PER_LEVEL = 5000
NUM_EASY_LEVELS = len(XP_PER_EASY_LEVEL)
XP_PER_PRESTIGE = sum(XP_PER_EASY_LEVEL) + XP_PER_LEVEL * (LEVELS_PER_PRESTIGE - NUM_EASY_LEVELS)

def totalExpForLevel(lvl: int) -> int:
    expDuringPres = (sum(x for i,x in enumerate(XP_PER_EASY_LEVEL) if i < lvlRespectingPres(lvl)) +
                     max(0, XP_PER_LEVEL * (lvlRespectingPres(lvl)-NUM_EASY_LEVELS)))
    return presForLevel(lvl) * XP_PER_PRESTIGE + expDuringPres

def presForLevel(lvl: int) -> int:
    return floor(lvl / LEVELS_PER_PRESTIGE)

def lvlRespectingPres(lvl: int) -> int:
    """
    E.g., for level 102, this function would return 2.
    """
    return lvl % LEVELS_PER_PRESTIGE