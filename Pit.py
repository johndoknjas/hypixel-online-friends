import math

import Utils

"""Some notes on how the pit leveling system works:
    - The PRESTIGE_XP values are the amount of total xp needed before each prestige.
    - Once a player prestiges, hypixel automatically gives them enough xp to go from level 0 to 1.
      E.g., 0-120 requires 65950 xp, while I-1 requires 65967 xp.
    - For players with 0 xp, they are 0-1 (rather than 0-0) since Hypixel does a workaround for this. Then
      once a player earns xp, hypixel gives an additional +15xp. E.g., a player starts the game at 0 xp and earns 16xp,
      which takes them to level 2 (requires 30xp total).
"""
# Got a lot of guidance from brooke-gill's pit repo.

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
# https://github.com/brooke-gill/pit/blob/307c126be78a5615b437205966dba13cbab3b787/xp2level.html#L93

def get_xp_req_for_prestige(prestige: int) -> int:
    """Returns the amount of total xp that must be earned before the specified prestige."""
    return 0 if prestige == 0 else PRESTIGE_XP[prestige-1]

def get_xp_reqs_for_levels(prestige: int) -> list[int]:
    """Returns a list of size 120, containing the total xp to reach levels 1-120 of the specified prestige."""
    levels_xp_reqs = [get_xp_req_for_prestige(prestige)] # this first element will be removed at the end of the function.
    for level in range(1, 121):
        prev_level_group_index = math.floor((level-1) / 10)
        additional_xp_needed_for_level = math.ceil(
            LVL_GROUP_MULTIPLIER[prev_level_group_index] * PRESTIGE_MULTIPLIER[prestige] / 100)
        levels_xp_reqs.append(additional_xp_needed_for_level + levels_xp_reqs[-1])
    if prestige == 0:
        levels_xp_reqs[1] = 0 # Workaround hypixel does for making 0 xp players be 0-1 and not 0-0.
    assert len(levels_xp_reqs) == 121
    return levels_xp_reqs[1:]

class PitStats:
    def __init__(self, pit_xp: int):
        assert pit_xp >= 0
        self._pit_xp = pit_xp
        self._prestige = next(i for i, xp_req in enumerate(PRESTIGE_XP) if xp_req >= self._pit_xp)

    def xp(self) -> int:
        return self._pit_xp
    
    def prestige(self) -> int:
        return self._prestige
    
    def prestige_roman(self) -> str:
        return Utils.num_to_roman(self.prestige())

    def level(self) -> int:
        xp_reqs_levels = get_xp_reqs_for_levels(self.prestige())
        for i in range(len(xp_reqs_levels)-1, -1, -1):
            if self.xp() >= xp_reqs_levels[i]:
                return i+1
        assert False
    
    def xp_gained_during_curr_pres(self) -> int:
        return self.xp() - get_xp_req_for_prestige(self.prestige())
    
    def percent_through_curr_pres(self) -> float:
        return self.xp_gained_during_curr_pres() / (get_xp_req_for_prestige(self.prestige()+1) -
                                                    get_xp_req_for_prestige(self.prestige()))
    
    def percent_overall_to_given_pres(self, prestige: int) -> float:
        return self.xp() / get_xp_req_for_prestige(prestige)