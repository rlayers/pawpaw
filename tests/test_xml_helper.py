import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

import pawpaw
import pawpaw.xml as xml
from tests.util import _TestIto, XML_TEST_SAMPLES


class TestQualifiedName(_TestIto):
    def test_from_src(self):
        for s in 'a', 'a:b':
            ito = pawpaw.Ito(s)
            parts = ito.str_split(':')
            if len(parts) == 1:
                parts.insert(0, None)
            expected = xml.QualifiedName(*parts)

            with self.subTest(src=ito):
                actual = xml.QualifiedName.from_src(ito)
                self.assertEqual(expected, actual)

            with self.subTest(src=s):
                actual = xml.QualifiedName.from_src(s)
                self.assertEqual(expected, actual)


class TestXmlHelper(_TestIto):
    def test_get_qualified_name(self):
        pass

    def test_get_xmlns(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, xml.XmlParser())
            with self.subTest(sample=root):
                xmlns = xml.XmlHelper.get_xmlns(root)
                xmlns = {str(k.local_part): str(v) for k, v in xmlns.items()}
                if sample.default_namespace is None:
                    self.assertIsNone(xmlns.get('xmlns'))
                else:
                    self.assertLessEqual({'xmlns': sample.default_namespace}.items(), xmlns.items())
                self.assertLessEqual(sample.root_prefix_map.items(), xmlns.items())

    def test_get_prefix_map_root(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, xml.XmlParser())
            with self.subTest(sample=root):
                self.assertDictEqual(sample.root_prefix_map, xml.XmlHelper.get_prefix_map(root))

    def test_get_prefix_map_composite(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, xml.XmlParser())
            with self.subTest(sample=root):
                actual = xml.XmlHelper.get_prefix_map(root)
                self.assertEqual(sample.root_prefix_map, actual)

                actual = {}
                for e in root.findall('.//'):
                    actual |= xml.XmlHelper.get_prefix_map(e)
                self.assertDictEqual(sample.descendants_composite_prefix_map, actual)

    def test_get_default_namespace(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, xml.XmlParser())
            with self.subTest(sample=root):
                if sample.default_namespace is None:
                    self.assertIsNone(xml.XmlHelper.get_default_namespace(root))
                else:
                    self.assertEqual(sample.default_namespace, str(xml.XmlHelper.get_default_namespace(root)))

    def test_get_element_text_if_found(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, xml.XmlParser())
            path = sample.text_containing_descendant_path

            with self.subTest(sample=root, path=path):
                expected = root.find(path).text
                actual = xml.XmlHelper.get_element_text_if_found(root, path)
                self.assertEqual(expected, actual)

            invalid_path = path + '/.[tag=""]'  # ensures path returns nothing
            with self.subTest(sample=root, path=invalid_path):
                actual = xml.XmlHelper.get_element_text_if_found(root, invalid_path)
                self.assertIsNone(actual)

    def test_reverse_find(self):
        for sample in XML_TEST_SAMPLES:
            root = ET.fromstring(sample.xml, xml.XmlParser())
            desc_path, anc_pred = sample.descendant_path_with_ancestor_predicate
            with self.subTest(sample=root, descendant_path=desc_path, ancestor_predicate=anc_pred):
                desc = root.find(desc_path)
                self.assertIsNotNone(desc)

                actual = xml.XmlHelper.reverse_find(desc, anc_pred)
                self.assertIsNotNone(actual)
