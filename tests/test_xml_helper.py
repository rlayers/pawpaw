import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

import pawpaw
from pawpaw import Ito
from pawpaw.xml import QualifiedName, XmlHelper, XmlParser
from tests.util import _TestIto, XML_TEST_SAMPLES


class TestQualifiedName(_TestIto):
    def test_from_src(self):
        for s in 'a', 'a:b':
            ito = pawpaw.Ito(s)
            parts = ito.str_split(':')
            if len(parts) == 1:
                parts.insert(0, None)
            expected = QualifiedName(*parts)

            with self.subTest(src=ito):
                actual = QualifiedName.from_src(ito)
                self.assertEqual(expected, actual)

            with self.subTest(src=s):
                actual = QualifiedName.from_src(s)
                self.assertEqual(expected, actual)


class TestXmlHelper(_TestIto):
    def test_get_qualified_name(self):
        pass

    def test_get_xmlns(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, XmlParser())
            with self.subTest(sample=root):
                xmlns = XmlHelper.get_xmlns(root)
                xmlns = {str(k.local_part): str(v) for k, v in xmlns.items()}
                if sample.default_namespace is None:
                    self.assertIsNone(xmlns.get('xmlns'))
                else:
                    self.assertLessEqual({'xmlns': sample.default_namespace}.items(), xmlns.items())
                self.assertLessEqual(sample.root_prefix_map.items(), xmlns.items())

    def test_get_prefix_map_root(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, XmlParser())
            with self.subTest(sample=root):
                self.assertDictEqual(sample.root_prefix_map, XmlHelper.get_prefix_map(root))

    def test_get_prefix_map_composite(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, XmlParser())
            with self.subTest(sample=root):
                actual = XmlHelper.get_prefix_map(root)
                self.assertEqual(sample.root_prefix_map, actual)

                actual = {}
                for e in root.findall('.//'):
                    actual |= XmlHelper.get_prefix_map(e)
                self.assertDictEqual(sample.descendants_composite_prefix_map, actual)

    def test_get_default_namespace(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, XmlParser())
            with self.subTest(sample=root):
                if sample.default_namespace is None:
                    self.assertIsNone(XmlHelper.get_default_namespace(root))
                else:
                    self.assertEqual(sample.default_namespace, str(XmlHelper.get_default_namespace(root)))

    def test_get_element_text_if_found(self):
        pass
