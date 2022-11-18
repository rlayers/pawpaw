import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

import pawpaw
from pawpaw.xml import XmlParser, ITO_DESCRIPTORS
from tests.util import _TestIto, XML_TEST_SAMPLES


class TestXmlParser(_TestIto):
    def setUp(self) -> None:
        self.parser = XmlParser()        
        
    def test_basic(self):
        sample = next(s for s in XML_TEST_SAMPLES if s.default_namespace is None)
        root_e = ET.fromstring(sample.xml, parser=self.parser)
        self.assertTrue(hasattr(root_e, 'ito'))
        
        root_i: pawpaw.Ito = root_e.ito
        self.assertEqual(ITO_DESCRIPTORS.ELEMENT, root_i.desc)
        
        self.assertIs(root_e, root_i.value())

    def test_nsamespace(self):
        sample = next(s for s in XML_TEST_SAMPLES if s.default_namespace is not None)
        root_e = ET.fromstring(sample.xml, parser=self.parser)
        
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
        sample = next(s for s in XML_TEST_SAMPLES if s.default_namespace is None)
        root_e = ET.fromstring(sample.xml, parser=self.parser)
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
