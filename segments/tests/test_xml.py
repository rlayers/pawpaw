import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

import segments
from segments.tests.util import _TestIto


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

        self.xml_et = """<?xml version="1.0"?>
        <data>
            <country name="Liechtenstein">
                <rank>1</rank>
            </country>
        </data>"""

        self.root_et = ET.fromstring(self.xml_et, parser=segments.xml.XmlParser())

    def test_ctor(self):
        parser = segments.xml.XmlParser()
        self.assertIsNotNone(parser)

    def test_basic(self):
        root = ET.fromstring(self.xml_et, parser=segments.xml.XmlParser())
        self.assertTrue(hasattr(root, '_ito'))
        ito_root: segments.Ito = root._ito
        self.assertEqual('Element', ito_root.desc)

        for country in root:
            ito_country = country._ito
            self.assertEqual('Element', ito_country.desc)
            start_tag = ito_country.children[0]
            self.assertTrue('Start_Tag', start_tag.desc)
            tag_ito = start_tag.children[0]
            self.assertTrue('Tag', tag_ito.desc)
            self.assertTrue(country.tag, tag_ito[:])
