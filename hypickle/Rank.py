from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy

from .Colours import Hex, ColourSpecs, colour_print

@dataclass
class RankColours:
    plus_colour: Hex | None
    """Represents the colour of any '+' chars that may be present in the rank."""
    player_name_brackets_colour: Hex | None
    """Represents the colour of the rank brackets and the player's name."""
    rank_colour: Hex | None
    """Represents the colour of the rank, excluding any potential '+' chars."""

class RankMap:
    _rank_map: dict[str | None, tuple[str, RankColours]] = {
        '§c[OWNER]': ('OWNER', RankColours(None, Hex.RED, Hex.RED)),
        'ADMIN': ('ADMIN', RankColours(None, Hex.RED, Hex.RED)),
        'GAME_MASTER': ('GM', RankColours(None, Hex.DARK_GREEN, Hex.DARK_GREEN)),
        'YOUTUBER': ('YOUTUBE', RankColours(None, Hex.RED, Hex.WHITE)),
        'VIP': ('VIP', RankColours(None, Hex.GREEN, Hex.GREEN)),
        'VIP_PLUS': ('VIP+', RankColours(Hex.GOLD, Hex.GREEN, Hex.GREEN)),
        'MVP': ('MVP', RankColours(None, Hex.AQUA, Hex.AQUA)),
        'MVP_PLUS': ('MVP+', RankColours(Hex.UNKNOWN, Hex.AQUA, Hex.AQUA)),
        'SUPERSTAR': ('MVP++', RankColours(Hex.UNKNOWN, Hex.UNKNOWN, Hex.UNKNOWN)),
        None: ('', RankColours(None, None, None))
    }
    @classmethod
    def json_rank_info(cls, key: str | None) -> tuple[str, RankColours]:
        """Returns the display string for a rank (without the brackets), as well as a RankColours
           object detailing the colours to print in."""
        return deepcopy(cls._rank_map[key])

class Rank:
    def __init__(self, json: dict) -> None:
        keys = ('prefix', 'rank', 'monthlyPackageRank', 'newPackageRank', 'packageRank')
        none_vals = (None, 'NONE', 'NORMAL')
        rank_map_key = next(
            (v for v in (json.get(k) for k in keys) if v not in none_vals), None
        )
        self._display_rank, self._colours = RankMap.json_rank_info(rank_map_key)
        self._json = json

    def rank(self, with_brackets_and_space: bool) -> str:
        """Returns the rank that's displayed ('VIP', 'MVP+', '', etc)"""
        if not with_brackets_and_space or self._display_rank == '':
            return self._display_rank
        return f"[{self._display_rank}] "

    def rank_colour(self) -> Hex | None:
        if self._colours.rank_colour == Hex.UNKNOWN:
            assert self._display_rank == 'MVP++'
            self._colours.rank_colour = (
                Hex.AQUA if self._json.get('monthlyRankColor') == 'AQUA' else Hex.GOLD
            )
        return self._colours.rank_colour

    def plus_colour(self) -> Hex | None:
        if self._colours.plus_colour == Hex.UNKNOWN:
            assert self._display_rank in ('MVP+', 'MVP++')
            json_plus_colour = self._json.get('rankPlusColor')
            self._colours.plus_colour = (Hex.RED if json_plus_colour is None else
                                         next(c for c in Hex if json_plus_colour == c.name))
        return self._colours.plus_colour

    def name_and_bracket_colour(self) -> Hex | None:
        if self._colours.player_name_brackets_colour == Hex.UNKNOWN:
            self._colours.player_name_brackets_colour = self.rank_colour()
        return self._colours.player_name_brackets_colour

    def print_rank(self) -> None:
        rank = self.rank(False)
        bracket_colour = self.name_and_bracket_colour()
        rank_colour = self.rank_colour()
        if rank == '':
            return
        assert bracket_colour is not None and rank_colour is not None

        colour_print(ColourSpecs('[', bracket_colour))
        colour_print(ColourSpecs(rank.rstrip('+'), rank_colour))
        if '+' in rank:
            assert rank.count('+') <= 2
            assert (plus_colour := self.plus_colour()) is not None
            colour_print(ColourSpecs('+', plus_colour))
            if rank.count('+') == 2:
                colour_print(ColourSpecs('+', plus_colour))
        colour_print(ColourSpecs('] ', bracket_colour))
