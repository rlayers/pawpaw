import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat

import typing

import regex
from segments import Span, Ito, __version__
import segments.xml
from segments.itorator import Extract


# print(__version__)
# print(__version__.major)
# print(__version__.pre_release)
# print(__version__.asdict())
# exit(0)

def dump_itos(*itos: Ito, indent='', __str__: bool = True):
    for i, ito in enumerate(itos):
        s = f' .__str__():"{ito.__str__()}"' if __str__ else ''
        print(f'{indent}{i:,}: .span={ito.span} .desc="{ito.desc}"{s}"')
        dump_itos(*ito.children, indent=indent+'  ', __str__=__str__)


sample_xml = """<?xml version="1.0"?>
<data>
    <country name="Liechtenstein">
        <rank>1</rank>
        <year>2008</year>
        <gdppc>141100</gdppc>
        <neighbor name="Austria" direction="E"/>
        <neighbor name="Switzerland" direction="W"/>
    </country>
    <country name="Singapore">
        <rank>4</rank>
        <year>2011</year>
        <gdppc>59900</gdppc>
        <neighbor name="Malaysia" direction="N"/>
    </country>
    <country name="Panama">
        <rank>68</rank>
        <year>2011</year>
        <gdppc>13600</gdppc>
        <neighbor name="Costa Rica" direction="W"/>
        <neighbor name="Colombia" direction="E"/>
    </country>
</data>"""

sample_xml = """<?xml version="1.0"?>
<data>
    <country name="Liechtenstein">
        <rank>1</rank>
    </country>
</data>"""

root = ET.fromstring(sample_xml, parser=segments.xml.XmlParser())
dump_itos(root._ito)
exit(0)