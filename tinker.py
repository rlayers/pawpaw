import random
import typing

import regex
from segments import Span, Ito, __version__
from segments.xml import XmlParser
from segments.tests.util import RandSpans


# print(__version__)
# print(__version__.major)
# print(__version__.pre_release)
# print(__version__.asdict())
# exit(0)


def dump_itos(*itos: Ito, indent='', __str__: bool = True):
    for i, ito in enumerate(itos):
        s = f' .__str__():"{ito.__str__()}"' if __str__ else ''
        print(f'{indent}{i:,}: .span={ito.span} .descriptor="{ito.descriptor}{s}"')
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

NAME = r'(?P<Name>[^ />=]+)'
VALUE = r'="(?P<Value>[^"]+)"'
NAME_VALUE = NAME + VALUE

NS_NAME = r'(?:(?P<Namespace>[^: ]+):)?' + NAME
NS_NAME_VALUE = NS_NAME + VALUE

ns_tag = regex.compile(r'\<(?P<Tag>' + NS_NAME + r')', regex.DOTALL)
attribute = regex.compile(r'(?P<Attribute>' + NS_NAME_VALUE + r')', regex.DOTALL)

m = ns_tag.match('<country name="Liechtenstein">')
print(m.group('Tag'))
# m = attribute.match('<country name="Liechtenstein">')
# print(m.group('Attribute'))
m = attribute.match('name="Liechtenstein"')
print(m.group('Attribute'))
# exit(0)

import xml.etree.ElementTree as ET
root = ET.fromstring(sample_xml, parser=XmlParser())
# root = ET.fromstring(sample_xml)
dump_itos(root._ito)


