# Based off https://github.com/Plancke/hypixel-php/blob/master/src/util/Leveling.php

from math import sqrt, floor

import Utils

_BASE = 10000
_GROWTH = 2500
_PQ_PREFIX = _BASE/_GROWTH - 0.5

def getExactLevel(exp: float) -> float:
    return getLevelFloor(exp) + getPercentageToNextLevel(exp)

def getLevelFloor(exp: float) -> int:
    return floor(1-_PQ_PREFIX + sqrt(_PQ_PREFIX**2+(2/_GROWTH)*exp))
    """Expression in floor() finds the positive root of a quadratic equation:
       1250*level**2 + 6250*level - 7500 - exp = 0. However, the expression is simpler than the
       quadratic forumla expression I generated for this (though equivalent) - not sure how it was 
       derived.
    """

def getPercentageToNextLevel(exp: float):
    lv = getLevelFloor(exp)
    xp_earned_during_current_level = exp - getTotalExpToLevelFloor(lv)
    return xp_earned_during_current_level / getExpFromLevelToNext(lv)

def getTotalExpToLevelFloor(level: int) -> float:
    assert level >= 1
    return _BASE*(level-1) + _GROWTH * (Utils.sum_to_n(level-2) if level > 1 else 0)
    """Equivalent to:
    `return sum(getExpFromLevelToNext(lvl) for lvl in range(1, level))`
    as well as
    `return 1250*level**2 + 6250*level - 7500`
    """

def getExpFromLevelToNext(level: int):
    assert level >= 1
    return _BASE + _GROWTH * (level-1)