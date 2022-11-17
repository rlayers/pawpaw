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


class TestXmlHlper(_TestIto):
    def test_get_qualified_name(self):
        pass

    def test_get_xmlns(self):
        sample = next(s for s in XML_TEST_SAMPLES if s.default_namespace is not None)
        root = ET.fromstring(sample.xml, XmlParser())
        xmlns = XmlHelper.get_xmlns(root)
        xmlns = {str(k.local_part): str(v) for k, v in xmlns.items()}
        self.assertDictContainsSubset({'xmlns': sample.default_namespace}, xmlns)
        self.assertDictContainsSubset(sample.prefix_map, xmlns)

    def test_get_prefix_map(self):
        sample = next(s for s in XML_TEST_SAMPLES if s.default_namespace is not None)
        root = ET.fromstring(sample.xml, XmlParser())
        self.assertDictEqual(sample.prefix_map, XmlHelper.get_prefix_map(root))

    def test_get_default_namespace(self):
        sample = next(s for s in XML_TEST_SAMPLES if s.default_namespace is not None)
        root = ET.fromstring(sample.xml, XmlParser())
        self.assertEqual(sample.default_namespace, str(XmlHelper.get_default_namespace(root)))

    def test_get_element_text_if_found(self):
        pass

