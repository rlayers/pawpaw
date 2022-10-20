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


@dataclass
class AnsiColorCodes:
    BLACK           = 30
    RED             = 31
    GREEN           = 32
    YELLOW          = 33
    BLUE            = 34
    MAGENTA         = 35
    CYAN            = 36
    WHITE           = 37
    RESET           = 39

    LIGHTBLACK_EX   = 90
    LIGHTRED_EX     = 91
    LIGHTGREEN_EX   = 92
    LIGHTYELLOW_EX  = 93
    LIGHTBLUE_EX    = 94
    LIGHTMAGENTA_EX = 95
    LIGHTCYAN_EX    = 96
    LIGHTWHITE_EX   = 97


class ForeColor:
    @classmethod
    def codestr(cls, code: int) -> str:
        return f'\033[{code}m'


for name in dir(AnsiColorCodes):
    if not name.startswith('_'):
        value = ForeColor.codestr(getattr(AnsiColorCodes, name))
        setattr(ForeColor, name, value)

print(ForeColor.YELLOW + 'Hello, world!')