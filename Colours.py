from typing import Optional
from enum import Enum
import rich.console
import rich.style

import Utils

console = rich.console.Console()

# Got the equivalent 3-digit hex codes from https://github.com/brooke-gill/pit/blob/main/levels.html
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
    PURPLE = "#aa00aa"
    ORANGE = "#ffaa00"
    PINK = "#ff55ff"
    GRAY = "#aaaaaa"
    DARK_GRAY = "#555555"
    WHITE = "#ffffff"
    BLACK = "#000000"

PIT_PRES_HEXES = [hex.value for hex in (
    Hex.GRAY, Hex.BLUE, Hex.YELLOW, Hex.ORANGE, Hex.RED, Hex.PURPLE, Hex.PINK, 
    Hex.WHITE, Hex.AQUA, Hex.DARK_BLUE, Hex.BLACK, Hex.DARK_RED, Hex.DARK_GRAY)
]
PIT_LVL_HEXES = [hex.value for hex in (
    Hex.GRAY, Hex.BLUE, Hex.DARK_AQUA, Hex.DARK_GREEN, Hex.GREEN, Hex.YELLOW, 
    Hex.ORANGE, Hex.RED, Hex.DARK_RED, Hex.PURPLE, Hex.PINK, Hex.WHITE, Hex.AQUA)
]
BW_PRES_HEXES = [hex.value for hex in (
    Hex.GRAY, Hex.WHITE, Hex.ORANGE, Hex.AQUA, Hex.DARK_GREEN, Hex.DARK_AQUA, 
    Hex.DARK_RED, Hex.PINK, Hex.BLUE, Hex.PURPLE)
]
assert (13,13,10) == (len(PIT_PRES_HEXES), len(PIT_LVL_HEXES), len(BW_PRES_HEXES))

def generate_rich_style(text_colour: str, background: Optional[str],
                        bold: bool, blink: bool) -> rich.style.Style:
    return rich.style.Style(color=text_colour, bgcolor=background, bold=bold, blink=blink)

def colour_print(text: str, colour_hex: str, background: Optional[str] = None, 
                 bold: bool = False, blink: bool = False, end: str = "") -> None:
    console.print(text, style=generate_rich_style(colour_hex, background, bold, blink),
                  end=end, highlight=False)

def pit_pres_hex_colour(pres: int) -> str:
    if pres == 0:
        return PIT_PRES_HEXES[0]
    elif pres == 50:
        return PIT_PRES_HEXES[-1]
    elif pres in (48, 49):
        return PIT_PRES_HEXES[-2]
    else:
        return PIT_PRES_HEXES[pres // 5 + 1]

def pit_lvl_hex_colour(lvl: int) -> str:
    return PIT_LVL_HEXES[lvl // 10]

def bw_star_hex_colour(star: int) -> str:
    if star >= 1000:
        return Hex.YELLOW.value
    return BW_PRES_HEXES[star // 100]

def roman_letters_hex_colour() -> str:
    return Hex.YELLOW.value

def print_pit_rank(rank: str) -> None:
    pres_colour = pit_pres_hex_colour(pres := Utils.get_prestige_from_pit_rank(rank))
    background = '#ffffff' if 45 <= pres <= 47 else None
    print(' ', end='')
    colour_print("[", pres_colour, background=background)
    if pres > 0:
        colour_print(Utils.num_to_roman(pres), roman_letters_hex_colour(), background=background)
        colour_print('-', pres_colour, background=background)
    lvl = Utils.get_level_from_pit_rank(rank)
    colour_print(str(lvl), pit_lvl_hex_colour(lvl), background=background, bold=(lvl >= 60))
    colour_print("]", pres_colour, background=background)
    print(' ' * (10 - len(rank) + (2 if pres == 0 else 0)), end='')

def print_bw_star(star: int) -> None:
    colour_print(f" [{star}:star:]", bw_star_hex_colour(star), bold = True, blink=(star >= 1000))
    print(' ' * (7 - len(str(star))), end='')