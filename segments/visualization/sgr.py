from dataclasses import dataclass, field
import enum
import typing


@dataclass
class Sgr:
    """
    SGR (Select Graphic Rendition) - see https://en.wikipedia.org/wiki/ANSI_escape_code
    """
    RESET_ALL = 0
    RESET     = -1

    @classmethod
    def encode(cls, *n: int) -> str:
        if len(n) == 0:
            n = '0'
        else:
            n = ';'.join(str(i) for i in n)
        return f'\033[{n}m'


@dataclass
class Intensity(Sgr):
    BOLD  = 1
    DIM   = 2
    RESET = 22


@dataclass
class Italic(Sgr):
    ON    = 3
    RESET = 23


@dataclass
class Underline(Sgr):
    SINGLE = 4
    DOUBLE = 21
    RESET  = 24


@dataclass
class Blink(Sgr):
    SLOW  = 5
    RAPID = 6
    RESET = 25


@dataclass
class Invert(Sgr):
    ON    = 7
    RESET = 27


@dataclass
class Conceal(Sgr):
    ON    = 8
    RESET = 28


@dataclass
class Strike(Sgr):
    SLOW  = 9
    RESET = 29


@dataclass
class Font(Sgr):
    RESET = 10
    ALT_1 = 11
    ALT_2 = 12
    ALT_3 = 13
    ALT_4 = 14
    ALT_5 = 15
    ALT_6 = 16
    ALT_7 = 17
    ALT_8 = 18
    ALT_9 = 19


class NamedColors(enum.IntEnum):
    BLACK  : int = 0
    RED    : int = 1
    GREEN  : int = 2
    YELLOW : int = 3
    BLUE   : int = 4
    MAGENTA: int = 5
    CYAN   : int = 6
    WHITE  : int = 7
    
    BRIGHT_BLACK  : int  = 60
    BRIGHT_GRAY   : int  = BRIGHT_BLACK
    BRIGHT_RED    : int  = 61
    BRIGHT_GREEN  : int  = 62
    BRIGHT_YELLOW : int  = 63
    BRIGHT_BLUE   : int  = 64
    BRIGHT_MAGENTA: int  = 65
    BRIGHT_CYAN   : int  = 66
    BRIGHT_WHITE  : int  = 67
    

@dataclass
class Fore(Sgr):
    _OFFSET = 30
    
    BLACK  : str = ''
    RED    : str = ''
    GREEN  : str = ''
    YELLOW : str = ''
    BLUE   : str = ''
    MAGENTA: str = ''
    CYAN   : str = ''
    WHITE  : str = ''
        
    _BY_IDX: int = 38
    
    BRIGHT_BLACK  : str  = ''
    BRIGHT_GRAY   : str  = ''
    BRIGHT_RED    : str  = ''
    BRIGHT_GREEN  : str  = ''
    BRIGHT_YELLOW : str  = ''
    BRIGHT_BLUE   : str  = ''
    BRIGHT_MAGENTA: str  = ''
    BRIGHT_CYAN   : str  = ''
    BRIGHT_WHITE  : str  = ''
        
    RESET = 39
    
    @classmethod
    def from_name(cls, name: str) -> str:
        code = getattr(NamedColors, name)
        code += cls._OFFSET
        return cls.encode(code)

    @classmethod
    def number(cls, n: int) -> str:
        return cls.encode(cls._BY_IDX, 5, n)

    @classmethod
    def rgb(cls, r: int = 0, g: int = 0, b: int = 0) -> str:
        return cls.encode(cls._BY_IDX, 2, r, g, b)


@dataclass
class Back(Fore):
    _OFFSET = Fore._OFFSET + 10
    _BY_IDX = Fore._BY_IDX + 10
    RESET = Fore.RESET + 10

for nc in NamedCOlors:
    for _class in Fore, Back:
        setattr(_class, nc.name, _class.from_name(nc.name))
    
for c in Sgr, Intensity, Italic, Underline, Blink, Invert, Conceal, Strike, Font, Fore, Back:
    for name in (n for n in dir(c) if n.isupper() and not n.startswith('_')):
        attr = getattr(c, name)
        val = c.encode(attr)
        setattr(c, name, val)
