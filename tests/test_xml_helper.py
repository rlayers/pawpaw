import sys
# Force Python XML parser, not faster C version so that we can hook methods
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
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            with self.subTest(xml_sample_index=sample_index):
                root = ET.fromstring(sample.xml, xml.XmlParser())
                xmlns = xml.XmlHelper.get_xmlns(root)
                xmlns = {str(k.local_part): str(v) for k, v in xmlns.items()}
                if sample.default_namespace is None:
                    self.assertIsNone(xmlns.get('xmlns'))
                else:
                    self.assertLessEqual({'xmlns': sample.default_namespace[1:-1]}.items(), xmlns.items())
                self.assertLessEqual(sample.root_prefix_map.items(), xmlns.items())

    def test_get_prefix_map_root(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            with self.subTest(xml_sample_index=sample_index):
                root = ET.fromstring(sample.xml, xml.XmlParser())
                self.assertDictEqual(sample.root_prefix_map, xml.XmlHelper.get_prefix_map(root))

    def test_get_prefix_map_composite(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            with self.subTest(xml_sample_index=sample_index):
                root = ET.fromstring(sample.xml, xml.XmlParser())
                actual = xml.XmlHelper.get_prefix_map(root)
                self.assertEqual(sample.root_prefix_map, actual)

                actual = {}
                for e in root.findall('.//'):
                    actual |= xml.XmlHelper.get_prefix_map(e)
                self.assertDictEqual(sample.descendants_composite_prefix_map, actual)

    def test_get_default_namespace(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            depth = 0
            element = ET.fromstring(sample.xml, xml.XmlParser())
            while element is not None:
                with self.subTest(xml_sample_index=sample_index, depth=depth):
                    if sample.default_namespace is None:
                        self.assertIsNone(xml.XmlHelper.get_default_namespace(element))
                    else:
                        self.assertEqual(sample.default_namespace, str(xml.XmlHelper.get_default_namespace(element)))
                depth += 1
                element = element.find('*')

    def test_get_element_text_if_found(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            path = sample.text_containing_descendant_path
            with self.subTest(xml_sample_index=sample_index, path=path):
                root = ET.fromstring(sample.xml, xml.XmlParser())
                expected = root.find(path).text
                actual = xml.XmlHelper.get_element_text_if_found(root, path)
                self.assertEqual(expected, actual)

            invalid_path = path + '/.[tag=""]'  # ensures path returns nothing
            with self.subTest(xml_sample_index=sample_index, path=invalid_path):
                actual = xml.XmlHelper.get_element_text_if_found(root, invalid_path)
                self.assertIsNone(actual)

    def test_get_parent_element(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            root = ET.fromstring(sample.xml, xml.XmlParser())
            
            depth = 0
            with self.subTest(xml_sample_index=sample_index, depth=depth):
                self.assertIsNone(xml.XmlHelper.get_parent_element(root))

            parent = root
            while (child := parent.find('*')) is not None:
                depth += 1
                with self.subTest(xml_sample_index=sample_index, depth=depth):
                    actual = xml.XmlHelper.get_parent_element(child)
                    self.assertIs(parent, actual)
                parent = child

    def test_reverse_find(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            desC_QPATH, anc_pred = sample.descendant_path_with_ancestor_predicate
            with self.subTest(xml_sample_index=sample_index, descendant_path=desC_QPATH, ancestor_predicate=anc_pred):
                root = ET.fromstring(sample.xml, xml.XmlParser())

                desc = root.find(desC_QPATH)
                self.assertIsNotNone(desc)

                actual = xml.XmlHelper.reverse_find(desc, anc_pred)
                self.assertIsNotNone(actual)
