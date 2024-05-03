# Based off https://github.com/Plancke/hypixel-php/blob/master/src/util/Leveling.php and
# https://github.com/Snuggle/hypixel.py/blob/main/leveling.py

from __future__ import annotations
import math
from typing import Optional, Callable

class QuadraticFunc:
    def __init__(self, a: float, b: float, c: float,
                 req_for_x_vals: Optional[Callable[[float], bool]] = None,
                 req_for_y_vals: Optional[Callable[[float], bool]] = None) -> None:
        "Represents some function: y = ax^2 + bx + c"
        self.a, self.b, self.c = a, b, c
        self.req_for_x_vals, self.req_for_y_vals = req_for_x_vals, req_for_y_vals

    def y_val(self, x_val: float) -> float:
        if self.req_for_x_vals:
            assert self.req_for_x_vals(x_val)
        return self.a*x_val**2 + self.b*x_val + self.c

    def x_vals(self, y_val: float) -> tuple[float, float]:
        """Returns the roots of the equation when substituting `y_val` for y."""
        # Need to make a quadratic equation. Do this by substituting y_val for y,
        # then subtracting it from both sides. This just makes c become self.c - y.
        if self.req_for_y_vals:
            assert self.req_for_y_vals(y_val)
        a, b, c = self.a, self.b, self.c - y_val
        sqrt_exp = math.sqrt(b**2 - 4*a*c)
        return ((-b+sqrt_exp)/(2*a), (-b-sqrt_exp)/(2*a))

_BASE = 10000
_GROWTH = 2500
_QUADRATIC_FUNC = QuadraticFunc(_GROWTH/2, _BASE - 1.5*_GROWTH, _GROWTH - _BASE,
                                lambda x: type(x) == int and 1 <= x <= 10000,
                                lambda y: type(y) == int and 0 <= y <= 10**12)
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

def getLevelFloor(exp: int) -> int:
    return math.floor(next(l for l in _QUADRATIC_FUNC.x_vals(exp) if l >= 1))

def getExactLevel(exp: int) -> float:
    return getLevelFloor(exp) + getPercentageToNextLevel(exp)

def getPercentageToNextLevel(exp: int) -> float:
    lvl = getLevelFloor(exp)
    xp_earned_during_current_level = exp - getTotalExpToLevelFloor(lvl)
    return xp_earned_during_current_level / getExpFromLevelToNext(lvl)
