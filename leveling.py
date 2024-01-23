# Based off https://github.com/Plancke/hypixel-php/blob/master/src/util/Leveling.php

from math import floor

import Utils

_BASE = 10000
_GROWTH = 2500
_QUADRATIC_FUNC = Utils.QuadraticFunc(_GROWTH/2, _BASE - 1.5*_GROWTH, _GROWTH - _BASE)
"""Represents the total xp as a function of level. Note that for decimal values of level in this
   function, they won't be the 'exact' level hypixel records. So for finding the level, this
   object should only be used to find the floor. Conversely for finding xp, only int values
   for level should be supplied."""

def getExactLevel(exp: float) -> float:
    return getLevelFloor(exp) + getPercentageToNextLevel(exp)

def getLevelFloor(exp: float) -> int:
    return floor(_QUADRATIC_FUNC.x_vals(exp, True)[0])

def getPercentageToNextLevel(exp: float):
    lv = getLevelFloor(exp)
    xp_earned_during_current_level = exp - getTotalExpToLevelFloor(lv)
    return xp_earned_during_current_level / getExpFromLevelToNext(lv)

def getTotalExpToLevelFloor(level: int) -> float:
    assert level >= 1
    return _QUADRATIC_FUNC.y_val(level)

def getExpFromLevelToNext(level: int):
    assert level >= 1
    return _BASE + _GROWTH * (level-1)