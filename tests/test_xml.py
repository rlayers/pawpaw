import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

import pawpaw
from pawpaw.xml import XmlParser, ITO_DESCRIPTORS
from tests.util import _TestIto


class TestXml(_TestIto):
    def setUp(self) -> None:
        self.parser = XmlParser()        
        
        # Sample xml taken from https://docs.python.org/3/library/xml.etree.elementtree.html
        self.xml_no_ns = \
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

        # Taken from https://docs.python.org/3/library/xml.etree.elementtree.html
        self.xml_ns = \
"""<?xml version="1.0"?>
<actors xmlns:fictional="http://characters.example.com"
        xmlns="http://people.example.com">
    <actor>
        <name>John Cleese</name>
        <fictional:character>Lancelot</fictional:character>
        <fictional:character>Archie Leach</fictional:character>
    </actor>
    <actor>
        <name>Eric Idle</name>
        <fictional:character>Sir Robin</fictional:character>
        <fictional:character>Gunther</fictional:character>
        <fictional:character>Commander Clement</fictional:character>
    </actor>
</actors>"""
        
    def test_basic(self):
        root_e = ET.fromstring(self.xml_no_ns, parser=self.parser)
        self.assertTrue(hasattr(root_e, 'ito'))
        
        root_i: pawpaw.Ito = root_e.ito
        self.assertEqual(ITO_DESCRIPTORS.ELEMENT, root_i.desc)
        
        self.assertIs(root_e, root_i.value())

    def test_nsamespace(self):
        root_e = ET.fromstring(self.xml_ns, parser=self.parser)
        
        first_start_tag = root_e.ito.find(f'**[d:' + pawpaw.xml.ITO_DESCRIPTORS.START_TAG + ']')
        self.assertIsNotNone(first_start_tag)
        
        first_attr = first_start_tag.find(f'**[d:' + pawpaw.xml.ITO_DESCRIPTORS.ATTRIBUTE + ']')
        self.assertIsNotNone(first_attr)
        self.assertEqual(3, len(first_attr.children))
        
        ns = first_attr.find('*')
        self.assertIsNotNone(ns)
        self.assertEqual(ns.desc, pawpaw.xml.ITO_DESCRIPTORS.NAMESPACE)
        self.assertEqual('xmlns', str(ns))
        
        name = ns.find('>')
        self.assertIsNotNone(name)
        self.assertEqual(name.desc, pawpaw.xml.ITO_DESCRIPTORS.NAME)
        self.assertEqual('fictional', str(name))
        
        value = name.find('>')
        self.assertIsNotNone(value)
        self.assertEqual(value.desc, pawpaw.xml.ITO_DESCRIPTORS.VALUE)
        self.assertEqual('http://characters.example.com', str(value))
        
    def test_hiearchical(self):
        root_e = ET.fromstring(self.xml_no_ns, parser=self.parser)
        root_i: pawpaw.Ito = root_e.ito
            
        expected = root_e.findall('country')
        actual = [i.value() for i in root_i.find_all(f'*[d:{ITO_DESCRIPTORS.ELEMENT}]')]
        self.assertEqual(len(expected), len(actual))
        for e, a in zip(expected, actual):
            self.assertIs(e, a)
            
        expected = root_e.findall('.//neighbor')
        actual = [i.value() for i in root_i.find_all(f'**[d:{ITO_DESCRIPTORS.ELEMENT}]' + '{*[d:' + ITO_DESCRIPTORS.START_TAG + ']/*[s:neighbor]&[i:0]}')]
        self.assertEqual(len(expected), len(actual))
        for e, a in zip(expected, actual):
            self.assertIs(e, a)
