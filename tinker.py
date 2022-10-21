import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import segments
import sgr
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


# TESTING

for effect in sgr.Intensity, sgr.Italic, sgr.Underline, sgr.Blink, sgr.Invert, sgr.Conceal, sgr.Strike, sgr.Font, sgr.Fore, sgr.Back:
    print(f'{effect.__name__.upper()}')
    for name in filter(lambda n: n.isupper() and not n.startswith('_') and not n.startswith('RESET'), dir(effect)):
        attr = getattr(effect, name)
        print(f'\t{name}: Before Sgr... {attr}Sgr applied!{effect.RESET} Sgr turned off.')
    print()

from random import randint

for line in range(1, 50):
    for color in sgr.Fore, sgr.Back:
        for col in range(1, 120):
            print(color.rgb(randint(0, 255), randint(0, 255), randint(0, 255)), end='')
            print(chr(ord('A') + randint(0, 25)) + color.RESET, end='')
        print()
exit()

s = 'Hello, world!'
# print(Back.BLUE + s + Back.RESET)
print(sgr.Back.rgb(255, 0, 255) + s + sgr.Back.RESET)
print(sgr.Back.number(127) + s + sgr.Back.RESET)
print()