import sys
# Force Python XML parser, not faster C version so that we can hook methods
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
import html

from pawpaw import Ito, Span, xml
from tests.util import _TestIto, XML_TEST_SAMPLES


class TestXmlParser(_TestIto):
    def test_basic(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            with self.subTest(xml_sample_index=sample_index):
                root_e = ET.fromstring(sample.xml, parser=xml.XmlParser())
                self.assertTrue(hasattr(root_e, 'ito'))

                root_i: Ito = root_e.ito
                self.assertEqual(xml.descriptors.ELEMENT, root_i.desc)

                self.assertIs(root_e, root_i.value())

    def test_namespace(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            with self.subTest(xml_sample_index=sample_index):
                root_e = ET.fromstring(sample.xml, parser=xml.XmlParser())

                start_tag = root_e.ito.find(f'**[d:' + xml.descriptors.START_TAG + ']')
                self.assertIsNotNone(start_tag)

                for attr in start_tag.find_all(f'**[d:' + xml.descriptors.ATTRIBUTE + ']'):
                    if attr is not None:
                        expected = [xml.descriptors.TAG, xml.descriptors.VALUE]
                        self.assertListEqual(expected, [i.desc for i in attr.children])

                        expected = [xml.descriptors.NAME]
                        tag = attr.children[0]
                        if tag.str_find(':') >= 0:
                            expected.insert(0, xml.descriptors.NAMESPACE)
                        self.assertListEqual(expected, [i.desc for i in tag.children])

    def test_hiearchical(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            with self.subTest(xml_sample_index=sample_index):
                root_e = ET.fromstring(sample.xml, parser=xml.XmlParser())

                root_i: Ito = root_e.ito
                self.assertIsNotNone(root_i)
                self.assertIs(root_e, root_i.value())

                for child_e in root_e.findall('.//'):
                    child_i = child_e.ito
                    self.assertIsNotNone(child_i)
                    self.assertIs(child_e, child_i.value())

    def test_values(self):
        for sample_index, sample in enumerate(XML_TEST_SAMPLES):
            with self.subTest(xml_sample_index=sample_index):
                root = ET.fromstring(sample.xml, parser=xml.XmlParser()).ito
                for ito in root.find_all('**!![d:' + ','.join((xml.descriptors.ELEMENT, xml.descriptors.TAG)) + ']'):
                    desc = ito.desc
                    with self.subTest(ito_desc=desc, ito_span=ito.span):
                        if desc == xml.descriptors.ELEMENT:
                            self.assertIsInstance(ito.value(), ET.Element)
                        elif desc == xml.descriptors.TAG:
                            self.assertIsInstance(ito.value(), xml.QualifiedName)

    def test_tails(self):
        # xml fragment taken from https://docs.python.org/3/library/xml.etree.elementtree.html
        fragment = '<?xml version="1.0"?><a><b>1<c>2<d/>3</c></b>4</a>'
        root = ET.fromstring(fragment, parser=xml.XmlParser())
        for descendant in root.findall('.//'):
            next_sibling = descendant.ito.find('>')
            if descendant.tail is None:
                self.assertTrue(next_sibling is None or next_sibling.desc != xml.descriptors.TEXT)
            else:
                self.assertEqual(descendant.tail, str(next_sibling))

    def test_xml_entity_references(self):
        # Ensure that entity references (e.g., "&amp;") don't cause issues with span computations and Ito construction
        sample = \
"""<?xml version="1.0" encoding="UTF-8"?>
<nodes>
    beans &amp; franks
    <math>1 &lt; 2</math>
    <music type="R&amp;B" />
    Q&amp;A
</nodes>"""
        root = ET.fromstring(sample, parser=xml.XmlParser())

        # First make sure our xml looks correct with de-escaped references for its text & tails
        self.assertEqual(root.text.strip(), html.unescape('beans &amp; franks'))
        self.assertEqual(root[0].text, html.unescape('1 &lt; 2'))
        self.assertEqual(root[-1].attrib['type'], html.unescape('R&amp;B'))
        self.assertEqual(root[-1].tail.strip(), html.unescape('Q&amp;A'))

        # Now compare html escaped xml text & tails to corresponding Itos
        self.assertEqual(html.escape(root.text), root.ito.find(f'*[d:{xml.descriptors.TEXT}]').__str__())
        self.assertEqual(html.escape(root[0].text), root[0].ito.find(f'*[d:{xml.descriptors.TEXT}]').__str__())
        self.assertEqual(html.escape(root[-1].attrib['type']), root[-1].ito.find(f'**[d:{xml.descriptors.ATTRIBUTE}]/*[d:{xml.descriptors.VALUE}]').__str__())
        self.assertEqual(html.escape(root[-1].tail), root.ito.find(f'-*[d:{xml.descriptors.TEXT}]').__str__())

    def test_xml_comments(self):
        # Ensure that encoded text (e.g., "&amp;") doesn't cause problems with span computations
        comment = '<!--Here is a comment-->'
        text = 'Here is some text'
        sample = '<?xml version="1.0" encoding="UTF-8"?><a>' + comment + text + '</a>'

        # root = ET.fromstring(sample, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
        root = ET.fromstring(sample, parser=xml.XmlParser())
        self.assertEqual(root.text, text)

        text_ito = root.ito.find(f'*[d:{xml.descriptors.TEXT}]')
        self.assertIsNotNone(text_ito)
        self.assertEqual(comment + text, str(text_ito))
