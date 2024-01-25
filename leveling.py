# Based off https://github.com/Plancke/hypixel-php/blob/master/src/util/Leveling.php

from math import floor

from Graphing import QuadraticFunc

_BASE = 10000
_GROWTH = 2500
_QUADRATIC_FUNC = QuadraticFunc(_GROWTH/2, _BASE - 1.5*_GROWTH, _GROWTH - _BASE,
                                lambda x: x in range(1,10000), lambda y: int(y) == y >= 0)
"""Represents the total xp as a function of level. Note that for decimal values of level in this
   function, they won't be the 'exact' level hypixel records. So for finding the level, this
   object should only be used to find the floor. Conversely for finding xp, only int values
   for level should be supplied."""

def getTotalExpToLevelFloor(level: int) -> int:
    xp = _QUADRATIC_FUNC.y_val(level)
    assert int(xp) == xp
    return int(xp)

def getExpFromLevelToNext(level: int) -> int:
    return getTotalExpToLevelFloor(level+1) - getTotalExpToLevelFloor(level)

def getLevelFloor(exp: float) -> int:
    return floor(next(l for l in _QUADRATIC_FUNC.x_vals(exp) if l >= 1))

def getExactLevel(exp: float) -> float:
    return getLevelFloor(exp) + getPercentageToNextLevel(exp)

def getPercentageToNextLevel(exp: float) -> float:
    lvl = getLevelFloor(exp)
    xp_earned_during_current_level = exp - getTotalExpToLevelFloor(lvl)
    return xp_earned_during_current_level / getExpFromLevelToNext(lvl)