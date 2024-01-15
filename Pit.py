import math

import Utils

# Got these values from: https://github.com/brooke-gill/pit/blob/307c126be78a5615b437205966dba13cbab3b787/xp2level.html#L93
LVL_GROUP_MULTIPLIER = [15, 30, 50, 75, 125, 300, 600, 800, 900, 1000, 1200, 1500, 0]
PRESTIGE_MULTIPLIER = [100, 110, 120, 130, 140, 150, 175, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 
             1200, 1400, 1600, 1800, 2000, 2400, 2800, 3200, 3600, 4000, 4500, 5000, 7500, 10000, 10100, 
             10100, 10100, 10100, 10100, 20000, 30000, 40000, 50000, 75000, 100000, 125000, 150000, 
             175000, 200000, 300000, 500000, 1000000, 5000000, 10000000]
PRESTIGE_XP = [65950, 138510, 217680, 303430, 395760, 494700, 610140, 742040, 906930, 1104780, 1368580, 
               1698330, 2094030, 2555680, 3083280, 3676830, 4336330, 5127730, 6051030, 7106230, 8293330, 
               9612330, 11195130, 13041730, 15152130, 17526330, 20164330, 23132080, 26429580, 31375830, 
               37970830, 44631780, 51292730, 57953680, 64614630, 71275580, 84465580, 104250580, 130630580, 
               163605580, 213068080, 279018080, 361455580, 460380580,575793080, 707693080, 905543080, 
               1235293080, 1894793080, 5192293080,11787293080]

def convert_xp_to_prestige(pit_xp: int) -> int:
    return next(index for index, xp_req in enumerate(PRESTIGE_XP) if xp_req >= pit_xp)

def get_xp_req_for_prestige(prestige: int) -> int:
    """Returns the amount of total xp needed to get to level 1 of the specified prestige."""
    return 0 if prestige == 0 else PRESTIGE_XP[prestige-1]

def get_xp_reqs_for_levels(prestige: int) -> list[int]:
    """Returns a list of size 120; the ith element is the total xp required to reach level i+1 of the
       specified prestige."""
    levels_xp_reqs = [get_xp_req_for_prestige(prestige)]
    # This first element here is the amount of xp needed to get to level 1 of the specified prestige.
    for level in range(2, 121):
        prev_level_group_index = math.floor((level-1) / 10)
        additional_xp_needed_for_level = math.ceil(
            LVL_GROUP_MULTIPLIER[prev_level_group_index] * PRESTIGE_MULTIPLIER[prestige] / 100)
        levels_xp_reqs.append(additional_xp_needed_for_level + levels_xp_reqs[-1])
    return levels_xp_reqs

class PitStats:
    def __init__(self, pit_xp: int):
        self._pit_xp = pit_xp
        self._prestige = convert_xp_to_prestige(self._pit_xp)

    def xp(self) -> int:
        return self._pit_xp
    
    def prestige(self) -> int:
        return self._prestige
    
    def prestige_roman(self) -> str:
        return Utils.num_to_roman(self.prestige())

    def level(self) -> int:
        return sum(1 for xp_req in get_xp_reqs_for_levels(self.prestige()) if self.xp() >= xp_req)