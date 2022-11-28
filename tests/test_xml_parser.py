import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

import pawpaw
from pawpaw.xml import XmlParser, ITO_DESCRIPTORS
from tests.util import _TestIto, XML_TEST_SAMPLES


class TestXmlParser(_TestIto):
    def test_basic(self):
        for sample in XML_TEST_SAMPLES:
            with self.subTest(xml_source=sample.source):
                root_e = ET.fromstring(sample.xml, parser=XmlParser())
                self.assertTrue(hasattr(root_e, 'ito'))

                root_i: pawpaw.Ito = root_e.ito
                self.assertEqual(ITO_DESCRIPTORS.ELEMENT, root_i.desc)

                self.assertIs(root_e, root_i.value())

    def test_namespace(self):
        for sample in XML_TEST_SAMPLES:
            with self.subTest(xml_source=sample.source):
                root_e = ET.fromstring(sample.xml, parser=XmlParser())

                start_tag = root_e.ito.find(f'**[d:' + pawpaw.xml.ITO_DESCRIPTORS.START_TAG + ']')
                self.assertIsNotNone(start_tag)

                for attr in start_tag.find_all(f'**[d:' + pawpaw.xml.ITO_DESCRIPTORS.ATTRIBUTE + ']'):
                    if attr is not None:
                        eq_idx = attr.str_index('=')
                        if attr.str_find(':', end=eq_idx) < 0:
                            self.assertEqual(2, len(attr.children))
                            self.assertEqual(pawpaw.xml.ITO_DESCRIPTORS.NAME, attr.children[0].desc)
                            self.assertEqual(pawpaw.xml.ITO_DESCRIPTORS.VALUE, attr.children[1].desc)
                        else:
                            self.assertEqual(3, len(attr.children))
                            self.assertEqual(pawpaw.xml.ITO_DESCRIPTORS.NAMESPACE, attr.children[0].desc)
                            self.assertEqual(pawpaw.xml.ITO_DESCRIPTORS.NAME, attr.children[1].desc)
                            self.assertEqual(pawpaw.xml.ITO_DESCRIPTORS.VALUE, attr.children[2].desc)

    def test_hiearchical(self):
        for sample in XML_TEST_SAMPLES:
            with self.subTest(xml_source=sample.source):
                root_e = ET.fromstring(sample.xml, parser=XmlParser())

                root_i: pawpaw.Ito = root_e.ito
                self.assertIsNotNone(root_i)
                self.assertIs(root_e, root_i.value())

                for child_e in root_e.findall('.//'):
                    child_i = child_e.ito
                    self.assertIsNotNone(child_i)
                    self.assertIs(child_e, child_i.value())

    def test_tails(self):
        # xml fragment taken from https://docs.python.org/3/library/xml.etree.elementtree.html
        xml = '<?xml version="1.0"?><a><b>1<c>2<d/>3</c></b>4</a>'
        root = ET.fromstring(xml, parser=XmlParser())
        for descendant in root.findall('.//'):
            next_sibling = descendant.ito.find('>')
            if descendant.tail is None:
                self.assertTrue(next_sibling is None or next_sibling.desc != ITO_DESCRIPTORS.TEXT)
            else:
                self.assertEqual(descendant.tail, str(next_sibling))
