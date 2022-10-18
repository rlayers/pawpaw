import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

import segments

# print(segments.__version__)
# print(segments.__version__.major)
# print(segments.__version__.pre_release)
# print(segments.__version__._asdict())
# exit(0)

ito = segments.Ito('The quick brown fox', desc='root')
ito.children.add(*(ito.clone(i, i+1, 'char') for i, c in enumerate(ito)))
query_str = '**[d:char]'  # '*/**[d:foo]{**}'

# results = [*ito.find_all_ex(query_str)]
# for r in results:
#     print(f'{r}')

# query = segments.query.compile(query_str)
# results = [*query.find_all(ito)]
# for r in results:
#     print(f'{r}')
#


def dump_itos(*itos: segments.Ito, indent='', __str__: bool = True):
    for i, ito in enumerate(itos):
        s = f' .__str__():"{ito.__str__()}"' if __str__ else ''
        print(f'{indent}{i:,}: .span={ito.span} .desc="{ito.desc}"{s}"')
        dump_itos(*ito.children, indent=indent+'  ', __str__=__str__)


# Sample taken from https://docs.python.org/3/library/xml.etree.elementtree.html
sample_xml_no_ns = """<?xml version="1.0"?>
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
sample_xml_with_ns = """"<?xml version="1.0"?>
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

root = ET.fromstring(sample_xml_with_ns, parser=segments.xml.XmlParser())
dump_itos(root.ito)
