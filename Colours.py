from typing import Optional
from enum import Enum
import rich.console
import rich.style

import Utils

console = rich.console.Console()

# Got the equivalent 3-digit hex codes for pit prestiges and levels from
# https://github.com/brooke-gill/pit/blob/main/levels.html
class Hex(Enum):
    RED = "#ff5555"
    DARK_RED = "#aa0000"
    BLUE = "#5555ff"
    DARK_BLUE = "#0000aa"
    YELLOW = "#ffff55"
    GREEN = "#55ff55"
    DARK_GREEN = "#00aa00"
    AQUA = "#55ffff"
    DARK_AQUA = "#00aaaa"
    DARK_PURPLE = "#aa00aa"
    GOLD = "#ffaa00"
    LIGHT_PURPLE = "#ff55ff"
    GRAY = "#aaaaaa"
    DARK_GRAY = "#555555"
    WHITE = "#ffffff"
    BLACK = "#000000"
    UNKNOWN = "used for cases where there is a colour, but it's not known at the moment"

PIT_PRES_HEXES = (Hex.GRAY, Hex.BLUE, Hex.YELLOW, Hex.GOLD, Hex.RED, Hex.DARK_PURPLE, Hex.LIGHT_PURPLE,
                  Hex.WHITE, Hex.AQUA, Hex.DARK_BLUE, Hex.BLACK, Hex.DARK_RED, Hex.DARK_GRAY)
PIT_LVL_HEXES = (Hex.GRAY, Hex.BLUE, Hex.DARK_AQUA, Hex.DARK_GREEN, Hex.GREEN, Hex.YELLOW,
                 Hex.GOLD, Hex.RED, Hex.DARK_RED, Hex.DARK_PURPLE, Hex.LIGHT_PURPLE, Hex.WHITE, Hex.AQUA)
BW_PRES_HEXES = (Hex.GRAY, Hex.WHITE, Hex.GOLD, Hex.AQUA, Hex.DARK_GREEN, Hex.DARK_AQUA,
                 Hex.DARK_RED, Hex.LIGHT_PURPLE, Hex.BLUE, Hex.DARK_PURPLE)
assert (13,13,10) == (len(PIT_PRES_HEXES), len(PIT_LVL_HEXES), len(BW_PRES_HEXES))

class ColourSpecs:
    def __init__(self, text: str, text_colour: Hex, bg_colour: Optional[Hex] = None, 
                 bold: bool = False, blink: bool = False):
        self.text, self.style = text, rich.style.Style(color=text_colour.value, bold=bold, blink=blink,
                                                       bgcolor = bg_colour.value if bg_colour else None)

def generate_rich_style(text_colour: Hex, background: Optional[Hex],
                        bold: bool, blink: bool) -> rich.style.Style:
    return rich.style.Style(color=text_colour.value, bold=bold, blink=blink,
                            bgcolor = background.value if background is not None else None)

def colour_print(msg: ColourSpecs) -> None:
    console.print(msg.text, style=msg.style, end='', highlight=False)

def pit_pres_hex_colour(pres: int) -> Hex:
    if pres == 0:
        return PIT_PRES_HEXES[0]
    elif pres == 50:
        return PIT_PRES_HEXES[-1]
    elif pres in (48, 49):
        return PIT_PRES_HEXES[-2]
    else:
        return PIT_PRES_HEXES[pres // 5 + 1]

def pit_lvl_hex_colour(lvl: int) -> Hex:
    return PIT_LVL_HEXES[lvl // 10]

def bw_star_hex_colour(star: int) -> Hex:
    if star >= 1000:
        return Hex.YELLOW
    return BW_PRES_HEXES[star // 100]

def print_pit_rank(rank: str) -> None:
    pres_colour = pit_pres_hex_colour(pres := Utils.get_prestige_from_pit_rank(rank))
    background = Hex.WHITE if 45 <= pres <= 47 else None
    print(' ', end='')
    colour_print(ColourSpecs("[", pres_colour, bg_colour=background))
    if pres > 0:
        colour_print(ColourSpecs(Utils.num_to_roman(pres), Hex.YELLOW, bg_colour=background))
        colour_print(ColourSpecs('-', pres_colour, bg_colour=background))
    lvl = Utils.get_level_from_pit_rank(rank)
    colour_print(ColourSpecs(str(lvl), pit_lvl_hex_colour(lvl), bg_colour=background, bold=(lvl >= 60)))
    colour_print(ColourSpecs("]", pres_colour, bg_colour=background))
    print(' ' * (10 - len(rank) + (2 if pres == 0 else 0)), end='')

def print_bw_star(star: int) -> None:
    colour_print(ColourSpecs(f" [{star}:star:]", bw_star_hex_colour(star), bold = True, blink=(star >= 1000)))
    print(' ' * (4 - len(str(star))), end='')