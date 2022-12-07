from dataclasses import dataclass, field
import enum
import typing

from pawpaw import Errors


"""
SGR (Select Graphic Rendition) - see https://en.wikipedia.org/wiki/ANSI_escape_code
"""
def encode(*n: int) -> str:
    if len(n) == 0:
        n = '0'
    else:
        n = ';'.join(str(i) for i in n)
    return f'\033[{n}m'

RESET_ALL: str = encode(0)

    
@dataclass(frozen=True)
class _Sgr:
    RESET : str


@dataclass(frozen=True)
class _Intensity(_Sgr):
    BOLD : str = encode(1)
    DIM  : str = encode(2)
    RESET: str = encode(22)


Intensity = _Intensity()


@dataclass(frozen=True)
class _Italic(_Sgr):
    ON   : str = encode(3)
    RESET: str = encode(23)


Italic = _Italic()


@dataclass(frozen=True)
class _Underline(_Sgr):
    SINGLE: str = encode(4)
    DOUBLE: str = encode(21)
    RESET : str = encode(24)


Underline = _Underline()


@dataclass(frozen=True)
class _Blink(_Sgr):
    SLOW : str = encode(5)
    RAPID: str = encode(6)
    RESET: str = encode(25)


Blink = _Blink()


@dataclass(frozen=True)
class _Invert(_Sgr):
    ON   : str = encode(7)
    RESET: str = encode(27)


Invert = _Invert()


@dataclass(frozen=True)
class _Conceal(_Sgr):
    ON   : str = encode(8)
    RESET: str = encode(28)


Conceal = _Conceal()


@dataclass(frozen=True)
class _Strike(_Sgr):
    SLOW : str = encode(9)
    RESET: str = encode(29)


Strike = _Strike()


@dataclass(frozen=True)
class _Font(_Sgr):
    ALT_1: str = encode(11)
    ALT_2: str = encode(12)
    ALT_3: str = encode(13)
    ALT_4: str = encode(14)
    ALT_5: str = encode(15)
    ALT_6: str = encode(16)
    ALT_7: str = encode(17)
    ALT_8: str = encode(18)
    ALT_9: str = encode(19)
    RESET: str = encode(10)


Font = _Font()


@dataclass
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


    class EightBit(int):
        """
            0-  7:  standard colors (as in ESC [ 30–37 m)
            8- 15:  high intensity colors (as in ESC [ 90–97 m)
            16-231:  6 × 6 × 6 cube (216 colors): 16 + 36 × r + 6 × g + b (0 ≤ r, g, b ≤ 5)
            232-255:  grayscale from dark to light in 24 steps
        """
        pass


Color = Colors.Named | Colors.Rgb | Colors.EightBit


@dataclass(frozen=True)
class Fore(_Sgr):
    _NAMED_OFFSET: int = 30
    _BY_IDX      : int = 38
    RESET        : str = encode(39)

    @classmethod
    def from_color(cls, src: Color) -> str:
        if isinstance(src, Colors.Named):
            nc = getattr(Colors.Named, src.name)
            return encode(nc.value + cls._NAMED_OFFSET)
        elif isinstance(src, Colors.Rgb):
            return encode(cls._BY_IDX, 2, *src)
        elif isinstance(src, Colors.EightBit):
            return encode(cls._BY_IDX, 5, src)
        else:
            raise Errors.parameter_invalid_type('src', src, Color)
        
    def __init__(self, src: Color):
        object.__setattr__(self, '_value', self.from_color(src))
        
    def __str__(self) -> str:
        return self._value


@dataclass(frozen=True)
class Back(Fore):
    _NAMED_OFFSET: int = Fore._NAMED_OFFSET + 10
    _BY_IDX      : int = Fore._BY_IDX + 10
    RESET        : str = encode(49)

    def __init__(self, src: Color):
        super().__init__(src)
