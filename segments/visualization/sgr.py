from dataclasses import dataclass, field
import enum
import typing


@dataclass
class Sgr:
    """
    SGR (Select Graphic Rendition) - see https://en.wikipedia.org/wiki/ANSI_escape_code
    """
    _RESET_ALL: int = 0
    RESET_ALL : str = ''
    _RESET    : int = -1
    RESET     :  str = ''

    @classmethod
    def encode(cls, *n: int) -> str:
        if len(n) == 0:
            n = '0'
        else:
            n = ';'.join(str(i) for i in n)
        return f'\033[{n}m'


@dataclass
class Intensity(Sgr):
    _BOLD: int = 1
    BOLD: str = ''

    _DIM: int = 2
    DIM: str = ''

    _RESET = 22


@dataclass
class Italic(Sgr):
    _ON   : int = 3
    ON    : str = ''
    _RESET: int = 23


@dataclass
class Underline(Sgr):
    _SINGLE: int  = 4
    SINGLE : str = ''
    _DOUBLE: int = 21
    DOUBLE : str = ''
    _RESET : int = 24


@dataclass
class Blink(Sgr):
    _SLOW: int = 5
    SLOW : str = ''
    _RAPID: int = 6
    RAPID: str = ''
    _RESET: int = 25


@dataclass
class Invert(Sgr):
    _ON   : int = 7
    ON    : str = ''
    _RESET: int = 27


@dataclass
class Conceal(Sgr):
    _ON   : int = 8
    ON    : str = ''
    _RESET: int = 28


@dataclass
class Strike(Sgr):
    _SLOW: int  = 9
    SLOW : str = ''
    _RESET = 29


@dataclass
class Font(Sgr):
    _RESET = 10
    _ALT_1: int = 11
    ALT_1 : str = ''
    _ALT_2: int = 12
    ALT_2 : str = ''
    _ALT_3: int = 13
    ALT_3 : str = ''
    _ALT_4: int = 14
    ALT_4 : str = ''
    _ALT_5: int = 15
    ALT_5 : str = ''
    _ALT_6: int = 16
    ALT_6 : str = ''
    _ALT_7: int = 17
    ALT_7 : str = ''
    _ALT_8: int = 18
    ALT_8 : str = ''
    _ALT_9: int = 19
    ALT_9 : str = ''


for c in Sgr, Intensity, Italic, Underline, Blink, Invert, Conceal, Strike, Font:
    for name in (n for n in dir(c)):
        target = name[1:]
        if name.isupper() and name.startswith('_') and hasattr(c, target):
            attr = getattr(c, name)
            val = c.encode(attr)
            setattr(c, target, val)


class Colors:
    class Named(enum.IntEnum):
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

    class Rgb(typing.NamedTuple):
        red: int
        green: int
        blue: int

    class EightBit:
        """
            0-  7:  standard colors (as in ESC [ 30–37 m)
            8- 15:  high intensity colors (as in ESC [ 90–97 m)
            16-231:  6 × 6 × 6 cube (216 colors): 16 + 36 × r + 6 × g + b (0 ≤ r, g, b ≤ 5)
            232-255:  grayscale from dark to light in 24 steps
        """


C_COLOR = Colors.Named | Colors.Rgb | Colors.EightBit


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
        
    _RESET = 39

    @classmethod
    def from_color(cls, src: C_COLOR) -> str:
        if isinstance(src, Colors.Named):
            nc = getattr(Colors.Named, src.name)
            return cls.encode(nc.value + cls._OFFSET)
        elif isinstance(src, Colors.Rgb):
            return cls.encode(cls._BY_IDX, 2, *src)
        elif isinstance(src, Colors.EightBit):
            return cls.encode(cls._BY_IDX, 5, src)


@dataclass
class Back(Fore):
    _OFFSET = Fore._OFFSET + 10
    _BY_IDX = Fore._BY_IDX + 10
    _RESET = Fore._RESET + 10


for _class in Fore, Back:
    setattr(_class, 'RESET', _class.encode(_class._RESET))
    for nc in Colors.Named:
        setattr(_class, nc.name, _class.from_color(nc))

print('foo')
    
