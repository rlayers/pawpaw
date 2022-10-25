import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import regex
import segments
from segments import Ito
from segments.visualization import sgr, Highlighter, dump


# # VERSION
#
# print(segments.__version__)
# print(segments.__version__.major)
# print(segments.__version__.pre_release)
# print(segments.__version__._asdict())
# exit(0)


# DUMPER

s = 'Hello, world!'
root = segment.Ito(s, desc='root')
for c in root.split(regex.compile(r'\s')):
    c.desc = 'child'
    root.children.add(c)
for dumper in dump.Compact(), dump.Json(), dump.Xml():
    name = type(dumper).__name__.upper()
    print(name)
    print('=' * len(name))
    print()
    print(dump.dumps(root))
    print()

exit(0)

    
# SGR    

for effect in sgr.Intensity, sgr.Italic, sgr.Underline, sgr.Blink, sgr.Invert, sgr.Conceal, sgr.Strike, sgr.Font, sgr.Fore, sgr.Back:
    print(f'{effect.__name__.upper()}')
    
    if effect in (sgr.Fore, sgr.Back):
        attrs = {nc.name: effect(nc) for nc in sgr.Colors.Named}
    else:
        names in filter(lambda n: n.isupper() and not n.startswith('_') and not n.startswith('RESET'), dir(effect)):
        attrs = {name: getattr(effect, name) for name in names}
        
    for name, attr in attrs.items():
        print(f'\t{name}: Before Sgr... {attr}Sgr applied!{effect.RESET} Sgr turned off.')
    
    print()

from random import randint

for line in range(1, 50):
    for color in sgr.Fore, sgr.Back:
        for col in range(1, 120):
            rgb = sgr.Colors.Rgb(randint(0, 255), randint(0, 255), randint(0, 255))
            print(effect(rgb), end='')
            print(chr(ord('A') + randint(0, 25)) + effect.RESET, end='')
        print()

exit()


# HIGHLIGHTER

s = 'The quick brown fox'
ito = segments.Ito(s)
ito.children.add(*ito.split(regex.compile('\s+')))

highlighter = Highlighter(
    sgr.Colors.Named.BRIGHT_CYAN,
    sgr.Colors.Named.CYAN,
    sgr.Colors.Named.BRIGHT_BLUE,
    sgr.Colors.Named.BLUE,
    sgr.Colors.Named.MAGENTA,
)
highlighter.print(ito)
