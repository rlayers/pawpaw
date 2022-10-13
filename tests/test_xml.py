import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

import segments
from tests.util import _TestIto


class TestXml(_TestIto):
    def setUp(self) -> None:
        # Sample xml taken from https://docs.python.org/3/library/xml.etree.elementtree.html
        self.xml_et = \
"""<?xml version="1.0"?>
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

    def test_ctor(self):
        parser = segments.xml.XmlParser()
        self.assertIsNotNone(parser)

    def test_basic(self):
        root_e = ET.fromstring(self.xml_et, parser=segments.xml.XmlParser())
        self.assertTrue(hasattr(root_e, 'ito'))
        
        root_i: segments.Ito = root_e.ito
        self.assertEqual('Element', root_i.desc)
        
        self.assertIs(root_e, root_i.value())

    def test_hiearchical(self):
        root_e = ET.fromstring(self.xml_et, parser=segments.xml.XmlParser())
        root_i: segments.Ito = root_e.ito        
            
        expected = root_e.findall('country')
        actual = [i.value() for i in root_i.find_all('*[d:Element]')]
        self.assertEqual(len(expected), len(actual))
        for e, a in zip(expected, actual):
            self.assertIs(e, a)
            
        expected = root_e.findall('.//neighbor')
        actual = [i.value() for i in root_i.find_all('**[d:Element]{*[d:Tag]&[i:0]&[s:neighbor]}')]
        actual = [i.value() for i in root_i.find_all('**[d:Element]{*[d:Start_Tag]/*[s:neighbor]&[i:0]}')]
        self.assertEqual(len(expected), len(actual))
        for e, a in zip(expected, actual):
            self.assertIs(e, a)