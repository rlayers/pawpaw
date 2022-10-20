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

