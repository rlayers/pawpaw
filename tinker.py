import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import regex
import pawpaw
from pawpaw import Ito
from pawpaw.visualization import sgr, Highlighter, dump


# # VERSION
#
# print(pawpaw.__version__)
# print(pawpaw.__version__.major)
# print(pawpaw.__version__.pre_release)
# print(pawpaw.__version__._asdict())
# exit(0)

from pawpaw.arborform.itorator import Desc, Extract, Split, Wrap

s = 'nine 9 ten 10 eleven 11 TWELVE 12 thirteen 13'
re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)(?: |$))+')

to_phrases = Split(regex.compile('(?<=\d )'), desc='Phrase')

to_wrd_nums = Split(regex.compile('\s'))
to_phrases.itor_children = to_wrd_nums

wrd_num_desc = Desc(lambda ito: 'number' if ito.str_isdecimal() else 'word')
to_wrd_nums.itor_next = wrd_num_desc

to_chr_dig = Extract(regex.compile(r'(?P<c>.)'))
wrd_num_desc.itor_children = to_chr_dig

chr_dig_desc = Desc(lambda ito: 'digit' if ito.str_isdecimal() else 'char')
to_chr_dig.itor_next = chr_dig_desc

root = Ito(s)
root.children.add(*to_phrases.traverse(root))

print(dump.Compact().dumps(root))
exit(0)

# DUMPER

s = 'Hello, world!'
root = pawpaw.Ito(s, desc='root')
for c in root.split(regex.compile(r'\s')):
    c.desc = 'child'
    root.children.add(c)
for dumper in dump.Compact(), dump.Json(), dump.Xml():
    name = type(dumper).__name__.upper()
    print(name)
    print('=' * len(name))
    print()
    print(dumper.dumps(root))
    print()

exit(0)

    
# SGR    

for effect in sgr.Intensity, sgr.Italic, sgr.Underline, sgr.Blink, sgr.Invert, sgr.Conceal, sgr.Strike, sgr.Font, sgr.Fore, sgr.Back:
    print(f'{effect.__name__.upper()}')
    
    if effect in (sgr.Fore, sgr.Back):
        attrs = {nc.name: effect(nc) for nc in sgr.Colors.Named}
    else:
        names = filter(lambda n: n.isupper() and not n.startswith('_') and not n.startswith('RESET'), dir(effect))
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
ito = pawpaw.Ito(s)
ito.children.add(*ito.split(regex.compile('\s+')))

highlighter = Highlighter(
    sgr.Colors.Named.BRIGHT_CYAN,
    sgr.Colors.Named.CYAN,
    sgr.Colors.Named.BRIGHT_BLUE,
    sgr.Colors.Named.BLUE,
    sgr.Colors.Named.MAGENTA,
)
highlighter.print(ito)
