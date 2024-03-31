import math
from typing import List, Optional, Tuple

from . import Utils

"""Some notes on how the pit leveling system works:
    - The PRESTIGE_XP values are the amount of total xp needed before each prestige.
    - Once a player prestiges, hypixel automatically gives them enough xp to go from level 0 to 1.
      E.g., 0-120 requires 65950 xp, while I-1 requires 65967 xp.
    - For players with 0 xp, they are 0-1 (rather than 0-0) since Hypixel does a workaround for this. Then
      once a player earns xp, hypixel gives an additional +15xp. E.g., a player starts the game at 0 xp and earns 16xp,
      which takes them to level 2 (requires 30xp total).
"""
# Got a lot of guidance from brooke-gill's pit repo.

LVL_GROUP_MULTIPLIER = (15, 30, 50, 75, 125, 300, 600, 800, 900, 1000, 1200, 1500, 0)
PRESTIGE_MULTIPLIER = (100, 110, 120, 130, 140, 150, 175, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000,
             1200, 1400, 1600, 1800, 2000, 2400, 2800, 3200, 3600, 4000, 4500, 5000, 7500, 10000, 10100,
             10100, 10100, 10100, 10100, 20000, 30000, 40000, 50000, 75000, 100000, 125000, 150000,
             175000, 200000, 300000, 500000, 1000000, 5000000, 10000000)
PRESTIGE_XP = (65950, 138510, 217680, 303430, 395760, 494700, 610140, 742040, 906930, 1104780, 1368580,
               1698330, 2094030, 2555680, 3083280, 3676830, 4336330, 5127730, 6051030, 7106230, 8293330,
               9612330, 11195130, 13041730, 15152130, 17526330, 20164330, 23132080, 26429580, 31375830,
               37970830, 44631780, 51292730, 57953680, 64614630, 71275580, 84465580, 104250580, 130630580,
               163605580, 213068080, 279018080, 361455580, 460380580,575793080, 707693080, 905543080,
               1235293080, 1894793080, 5192293080,11787293080)
# https://github.com/brooke-gill/pit/blob/307c126be78a5615b437205966dba13cbab3b787/xp2level.html#L93

def total_xp_req_for_pres(prestige: int) -> int:
    """Returns the amount of total xp that must be earned before the specified prestige."""
    return 0 if prestige == 0 else PRESTIGE_XP[prestige-1]

def total_xp_reqs_for_levels(prestige: int) -> List[int]:
    """Returns a list of size 120, containing the total xp to reach levels 1-120 of the specified prestige."""
    levels_xp_reqs = [total_xp_req_for_pres(prestige)] # this first element will be removed at the end of the function.
    for level in range(1, 121):
        prev_level_group_index = math.floor((level-1) / 10)
        additional_xp_needed_for_level = math.ceil(
            LVL_GROUP_MULTIPLIER[prev_level_group_index] * PRESTIGE_MULTIPLIER[prestige] / 100)
        levels_xp_reqs.append(additional_xp_needed_for_level + levels_xp_reqs[-1])
    if prestige == 0:
        levels_xp_reqs[1] = 0 # Workaround hypixel does for making 0 xp players be 0-1 and not 0-0.
    assert len(levels_xp_reqs) == 121
    return levels_xp_reqs[1:]

def xp_percent_levels() -> List[float]:
    """Returns a list of size 120, containing the percent through a prestige (in terms of xp)
       to reach a certain level."""
    pres = 1 # Any greater prestige works as well.
    xp_for_lvls = [xp - PRESTIGE_XP[pres-1] for xp in total_xp_reqs_for_levels(pres)]
    return [d * 100 for d in Utils.normalize_against_max_val(xp_for_lvls)]

def get_xp_req_for_rank(pit_rank: str) -> int:
    """pit_rank should be of the form: *roman number/decimal number* *-* *decimal number from 1 to 120*
    Will return an int representing the total xp needed to reach it."""
    pres, lvl = Utils.get_prestige_from_pit_rank(pit_rank), Utils.get_level_from_pit_rank(pit_rank)
    return total_xp_reqs_for_levels(pres)[lvl-1]

class PitStats:
    def __init__(self, pit_xp: int, playtime_kills_deaths: Optional[Tuple[int,int,int]] = None):
        """note: playtime measured in mins"""
        assert pit_xp >= 0
        self._pit_xp = pit_xp
        self._playtime_kills_deaths = playtime_kills_deaths
        """First elem stores the total pit playtime in mins, second elem is total #kills, third is total #deaths."""
        self._prestige = next(i for i, xp_req in enumerate(PRESTIGE_XP) if xp_req >= self._pit_xp)

    def xp(self) -> int:
        return self._pit_xp

    def prestige(self) -> int:
        return self._prestige

    def rank_string(self) -> str:
        return f"{Utils.num_to_roman(self.prestige())}-{self.level()}"

    def level(self) -> int:
        xp_reqs_levels = total_xp_reqs_for_levels(self.prestige())
        for i in range(len(xp_reqs_levels)-1, -1, -1):
            if self.xp() >= xp_reqs_levels[i]:
                return i+1
        assert False

    def xp_gained_during_curr_pres(self) -> int:
        return self.xp() - total_xp_req_for_pres(self.prestige())

    def xp_delta_req_for_curr_pres(self) -> int:
        """Returns the xp requirements for the curr prestige (not including past prestiges)."""
        return total_xp_req_for_pres(self.prestige()+1) - total_xp_req_for_pres(self.prestige())

    def percent_through_curr_pres(self) -> float:
        return self.xp_gained_during_curr_pres() / self.xp_delta_req_for_curr_pres()

    def percent_overall_to_given_pres(self, prestige: int) -> float:
        return self.xp() / total_xp_req_for_pres(prestige)

    def print_info(self) -> None:
        print(f"pit rank: {self.rank_string()}, pit xp: {self.xp()}")
        print(f"percent through current prestige: {Utils.percentify(self.percent_through_curr_pres())}")
        for i in range(1, 6):
            future_pres = self.prestige() + i
            if future_pres > 51:
                break
            print(f"Overall way through to prestige {future_pres}: ", end="")
            print(Utils.percentify(self.percent_overall_to_given_pres(future_pres)), end=", ")
        total_xp_for_120 = total_xp_reqs_for_levels(self.prestige())[-1]
        xp_after_kings = min(total_xp_for_120, self.xp() + 0.30326 * self.xp_delta_req_for_curr_pres())
        # 30.326% figure from https://pit.wiki/Kings_Quest
        print(f"King's quest would bring the rank to {PitStats(xp_after_kings).rank_string()}")
        xp_after_overdrive = min(total_xp_for_120, self.xp() + 4000)
        print(f"Overdrive would cover {round(4000 / self.xp_delta_req_for_curr_pres() * 100, 2)}% " +
              f"of the current prestige's xp requirements. It would bring the rank to " +
              f"{PitStats(xp_after_overdrive).rank_string()}")
        if not self._playtime_kills_deaths:
            print("\n")
            return
        playtime_mins, kills, deaths = self._playtime_kills_deaths
        playtime_hrs = playtime_mins / 60
        print(f"\npit playtime hours: {round(playtime_hrs, 3)}, ", end='')
        print(f"total kills: {kills}, KDR: {round(Utils.kdr_division(kills, deaths), 3)}, ", end='')
        if playtime_hrs > 0:
            print(f"K/hour: {round(kills / playtime_hrs, 3)}, ", end='')
            print(f"XP/hour: {round(self._pit_xp / playtime_hrs, 3)}, ", end='')
        print("\n")
