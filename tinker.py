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


import inspect
import typing
import types


def my_func(ito: Ito, match: regex.Match | None = None, fall_back: str = 'Ugh') -> str:
    return '...'.join([str(ito), str(match), str(fall_back)])




argspec = inspect.getfullargspec(my_func)
print(f'.args: {argspec.args}')
print(f'.defaults: {argspec.defaults}')
print(f'.kwonlyargs: {argspec.kwonlyargs}')
print(f'.kwonlydefaults: {argspec.kwonlydefaults}')
print(f'.annotations: {argspec.annotations}')
print()

s = 'abc'
ito = Ito(s)
re = regex.compile('.')
m = re.match(s)
# print(ito, re, m)

print(pawpaw.Types.invoke_desc_func(my_func, m, ito))
print(pawpaw.Types.invoke_desc_func(my_func, ito, m))
print(pawpaw.Types.invoke_desc_func(my_func, m, ito, 'fallback param val'))
exit(0)

vals = (ito, m)
target_param_vals = {}
for val in vals:
    val_type = type(val)
    for k, annotation in argspec.annotations.items():
        origin = typing.get_origin(annotation)
        print(f'val_type: {val_type}; annotation: {annotation}; result: ', end='')
        if origin is types.UnionType:
            result = val_type in typing.get_args(annotation)
        else:
            result = issubclass(val_type, annotation)
        print(result)
        if result:
            target_param_vals[k] = val_type
print(target_param_vals)
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
