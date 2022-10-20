import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import segments
import regex

# print(segments.__version__)
# print(segments.__version__.major)
# print(segments.__version__.pre_release)
# print(segments.__version__._asdict())
# exit(0)


def dump_itos(*itos: segments.Ito, indent='', __str__: bool = True):
    for i, ito in enumerate(itos):
        s = f' .__str__(): "{ito}"' if __str__ else ''
        print(f'{indent}{i:,}: .span={ito.span} .desc="{ito.desc}"{s}"')
        dump_itos(*ito.children, indent=indent+'  ', __str__=__str__)

"""
See: https://en.wikipedia.org/wiki/ANSI_escape_code
"""

@dataclass Sgr:  # SGR Renditin Codes
    @classmethod
    def _to_str(cls, *n: int) -> str:
        if len(n) == 0:
            n = '0'
        else:
            n = ';'.join(str(i) for i in n)
        return f'\033[{n}m'
    
@dataclass
class Style(Sgr):  
    RESET_ALL      = 0
    NORMAL         = RESET_ALL
    INVERT         = 7
    REVERSE_VIDEO  = INVERT
    CONCEAL        = 8
    HIDE           = CONCEAL
    STRIKE         = 9
    CROSSED_OUT    = STRIKE
    
@dataclass
class Italic(Sgr):
    ON  = 3
    OFF = 23

@dataclass
class Underline(Sgr):
    SINGLE = 4
    DOUBLE = 21
    NONE   = 24

@dataclass
class Intensity(Sgr):
    NORMAL = RESET
    BOLD   = 1
    FAINT  = 2
    DIM    = FAINT

@dataclass
class Blink(Sgr):
    SLOW    = 5
    RAPID   = 6
    NONE    = 25
    
@dataclass
class Font(Sgr):
    PRIMARY  = 10
    DEFAULT  = PRIMARY
    ALT_1    = 11
    ALT_2    = 12
    ALT_3    = 13
    ALT_4    = 14
    ALT_5    = 15
    ALT_6    = 16
    ALT_7    = 17
    ALT_8    = 18
    ALT_9    = 19

@dataclass
class Fore:
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
    
for c in (Style, Italic, Underline, Intensity, Blink, Font, Fore, Back):
    for name in (n for n in dir(c) if n.isupper() and not n.startswith('_')):
        attr = getattr(c, name)
        val = c._to_str(attr)
        setattr(c, name, val)
        
s = 'Hello, world!'
# print(Fore.RED + s + Fore.RESET)
print(Fore.rgb(0, 255, 255) + s + Fore.RESET)
print(Fore.number(222) + s + Fore.RESET)
print()

for effect in Style, Italic, Underline, Intensity, Blink, Font, Fore, Back:
    print(f'{effect.__name__.upper()}')
    for name in filter(lambda n: not n.startswith('_'), dir(effect)):
        attr = getattr(effect, name)
        print(f'\t{name}: {attr}{s}{Style.RESET}')
    print()
          
# print(Back.BLUE + s + Back.RESET)
print(Back.rgb(255, 0, 255) + s + Back.RESET)
print(Back.number(127) + s + Back.RESET)
print()
