from typing import Optional
from enum import Enum
import rich
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

PRES_HEXES = [hex.value for hex in (Hex.GRAY, Hex.BLUE, Hex.YELLOW, Hex.ORANGE, Hex.RED, Hex.PURPLE, Hex.PINK, 
                                    Hex.WHITE, Hex.AQUA, Hex.DARK_BLUE, Hex.BLACK, Hex.DARK_RED, Hex.DARK_GRAY)]
LVL_HEXES = [hex.value for hex in (Hex.GRAY, Hex.BLUE, Hex.DARK_AQUA, Hex.DARK_GREEN, Hex.GREEN, Hex.YELLOW, 
                                   Hex.ORANGE, Hex.RED, Hex.DARK_RED, Hex.PURPLE, Hex.PINK, Hex.WHITE, Hex.AQUA)]
assert len(PRES_HEXES) == len(LVL_HEXES) == 13

def generate_rich_style(text_colour: str, background: Optional[str], bold: bool) -> rich.style.Style:
    return rich.style.Style(color=text_colour, bgcolor=background, bold=bold)

def colour_print(text: str, colour_hex: str, background: Optional[str] = None, 
                 bold: bool = False, end: str = "") -> None:
    console.print(text, style=generate_rich_style(colour_hex, background, bold), end=end, highlight=False)

def emoji_print(emoji_name: str, end: str = "") -> None:
    """`emoji_name` must be one of the options that are listed by `python -m rich.emoji`."""
    rich.print(f":{emoji_name.strip(':')}:", end=end)

def pres_hex_colour(pres: int) -> str:
    if pres == 0:
        return PRES_HEXES[0]
    elif pres == 50:
        return PRES_HEXES[-1]
    elif pres in (48, 49):
        return PRES_HEXES[-2]
    else:
        return PRES_HEXES[pres // 5 + 1]

def lvl_hex_colour(lvl: int) -> str:
    return LVL_HEXES[lvl // 10]

def roman_letters_hex_colour() -> str:
    return PRES_HEXES[2]

def print_pit_rank(rank: str) -> None:
    pres_colour = pres_hex_colour(pres := Utils.get_prestige_from_pit_rank(rank))
    background = '#ffffff' if 45 <= pres <= 47 else None
    print(' ', end='')
    colour_print("[", pres_colour, background=background)
    if pres > 0:
        colour_print(Utils.num_to_roman(pres), roman_letters_hex_colour(), background=background)
        colour_print('-', pres_colour, background=background)
    lvl = Utils.get_level_from_pit_rank(rank)
    colour_print(str(lvl), lvl_hex_colour(lvl), background=background, bold=(lvl >= 60))
    colour_print("]", pres_colour, background=background)
    print(' ' * (10 - len(rank) + (2 if pres == 0 else 0)), end='')