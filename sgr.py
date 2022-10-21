from dataclasses import dataclass


@dataclass
class Sgr:
    """
    SGR (Select Graphic Rendition) - see https://en.wikipedia.org/wiki/ANSI_escape_code
    """
    RESET_ALL = 0
    RESET     = -1

    @classmethod
    def _to_str(cls, *n: int) -> str:
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


@dataclass
class Fore(Sgr):
    BLACK   = 30
    RED     = 31
    GREEN   = 32
    YELLOW  = 33
    BLUE    = 34
    MAGENTA = 35
    CYAN    = 36
    WHITE   = 37
    _BY_IDX = 38
    
    RESET = 39

    BRIGHT_BLACK   = 90
    BRIGHT_GRAY    = BRIGHT_BLACK
    BRIGHT_RED     = 91
    BRIGHT_GREEN   = 92
    BRIGHT_YELLOW  = 93
    BRIGHT_BLUE    = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN    = 96
    BRIGHT_WHITE   = 97

    @classmethod
    def number(cls, n: int) -> str:
        return cls._to_str(cls._BY_IDX, 5, n)

    @classmethod
    def rgb(cls, r: int = 0, g: int = 0, b: int = 0) -> str:
        return cls._to_str(cls._BY_IDX, 2, r, g, b)


@dataclass
class Back(Fore):
    ...


for name in (n for n in dir(Fore) if n.isupper()):
    attr = getattr(Fore, name)
    setattr(Back, name, attr + 10)
    
for c in Sgr, Intensity, Italic, Underline, Blink, Invert, Conceal, Strike, Font, Fore, Back:
    for name in (n for n in dir(c) if n.isupper() and not n.startswith('_')):
        attr = getattr(c, name)
        val = c._to_str(attr)
        setattr(c, name, val)
