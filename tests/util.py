from __future__ import annotations
import collections.abc
import random
import typing
from unittest import TestCase

import regex
from pawpaw import Span, Ito, Types


class IntIto(Ito):  # Used for derived class tests
    def value(self) -> typing.Any:
        return int(str(self))
    

class _TestIto(TestCase):
    @classmethod
    def add_chars_as_children(cls, ito: pawpaw.Ito, desc: str | None) -> None:
        ito.children.add(*(ito.clone(i, i + 1, desc) for i in range(*ito.span)))

    def matches_equal(self, first: regex.Match, second: regex.Match, msg: typing.Any = ...) -> None:
        if first is second:
            return
        
        self.assertListEqual([*first.regs], [*second.regs])
        self.assertEqual(first.group(0), second.group(0))
        self.assertSequenceEqual(first.groupdict().keys(), second.groupdict().keys())
        for v1, v2 in zip(first.groupdict().values(), second.groupdict().values()):
            self.assertEqual(v1, v2)
            
    def setUp(self) -> None:
        self.addTypeEqualityFunc(regex.Match, self.matches_equal)

        
class RandSpans:
    def __init__(
            self,
            size: Span = (1, 1),
            gap: Span = (0, 0),
    ):
        if not (isinstance(size, tuple) and len(size) == 2 and all(isinstance(i, int) for i in size)):
            raise TypeError('invalid \'size\'')
        if size[0] < 0 or size[1] < 1 or size[0] > size[1]:
            raise ValueError('invalid \'size\'')
        self.size = size

        if not (isinstance(gap, tuple) and len(gap) == 2 and all(isinstance(i, int) for i in gap)):
            raise TypeError('invalid \'gap\'')
        if (gap[0] < 0 and abs(gap[0]) >= size[0]) or (gap[1] < 0 and abs(gap[1]) >= size[0]):
            raise ValueError('invalid \'gap\'')
        self.gap = gap

    def generate(
            self,
            basis: int | collections.abc.Sized,
            start: int | None = None,
            stop: int | None = None
    ) -> typing.Iterable[Span]:
        i, stop = Span.from_indices(basis, start, stop)
        while i < stop:
            k = i + random.randint(*self.size)
            k = min(k, stop)
            yield Span(i, k)
            if k == stop:
                break
            i = k + random.randint(*self.gap)


class RandSubstrings(RandSpans):
    def __init__(
            self,
            size: Span = Span(1, 1),
            gap: Span = Span(0, 0),
    ):
        super().__init__(size, gap)

    def generate(self, string: str, start: int | None = None, stop: int | None = None) -> typing.Iterable[str]:
        for span in super().generate(string, start, stop):
            yield string[slice(*span)]


class XmlTestSample(typing.NamedTuple):
    source: str
    
    default_namespace: None | str
    
    # prefix_map of root node
    root_prefix_map: typing.Dict[str, str]
    
    # combined prefix_map of all non-root nodes
    descendants_composite_prefix_map: typing.Dict[str, str]
    
    # path to arbitrary descendant that has non-emtpy .text
    text_containing_descendant_path: str  
    
    # path to arbitrary descendant that can be reversed searched to find ancestor that matches predicate
    descendant_path_with_ancestor_predicate: typing.Tuple[str, str]

    xml: str


XML_TEST_SAMPLES: typing.List[XmlTestSample] = [
    XmlTestSample(
        source='https://docs.python.org/3/library/xml.etree.elementtree.html',
        default_namespace=None,
        root_prefix_map={},
        descendants_composite_prefix_map={},
        text_containing_descendant_path='.//year',
        descendant_path_with_ancestor_predicate=('.//gdppc', 'rank'),
        xml=
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
    ),

    XmlTestSample(
        source='https://docs.python.org/3/library/xml.etree.elementtree.html',
        default_namespace='http://people.example.com',
        root_prefix_map={'fictional': 'http://characters.example.com'},
        descendants_composite_prefix_map={},
        text_containing_descendant_path='.//{http://people.example.com}name',
        descendant_path_with_ancestor_predicate=('.//{http://characters.example.com}character', '{http://people.example.com}actor'),
        xml=
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
    ),

    XmlTestSample(
        source='https://www.xml.com/pub/a/1999/01/namespaces.html',
        default_namespace=None,
        root_prefix_map={'xdc': 'http://www.xml.com/books', 'h': 'http://www.w3.org/HTML/1998/html4'},
        descendants_composite_prefix_map={},
        text_containing_descendant_path='.//{http://www.xml.com/books}author',
        descendant_path_with_ancestor_predicate=('.//{http://www.xml.com/books}date', '@align'),
        xml='''
<h:html xmlns:xdc="http://www.xml.com/books"
        xmlns:h="http://www.w3.org/HTML/1998/html4">
 <h:head><h:title>Book Review</h:title></h:head>
 <h:body>
  <xdc:bookreview>
   <xdc:title>XML: A Primer</xdc:title>
   <h:table>
    <h:tr align="center">
     <h:td>Author</h:td><h:td>Price</h:td>
     <h:td>Pages</h:td><h:td>Date</h:td></h:tr>
    <h:tr align="left">
     <h:td><xdc:author>Simon St. Laurent</xdc:author></h:td>
     <h:td><xdc:price>31.98</xdc:price></h:td>
     <h:td><xdc:pages>352</xdc:pages></h:td>
     <h:td><xdc:date>1998/01</xdc:date></h:td>
    </h:tr>
   </h:table>
  </xdc:bookreview>
 </h:body>
</h:html>'''
    ),

    XmlTestSample(
        source='https://www.w3schools.com/xml/xml_namespaces.asp',
        default_namespace=None,
        root_prefix_map={},
        descendants_composite_prefix_map={'h': 'http://www.w3.org/TR/html4/', 'f': 'https://www.w3schools.com/furniture'},
        text_containing_descendant_path='.//{http://www.w3.org/TR/html4/}td',
        descendant_path_with_ancestor_predicate=('.//{https://www.w3schools.com/furniture}length', '{https://www.w3schools.com/furniture}name'),
        xml='''
<root>

<h:table xmlns:h="http://www.w3.org/TR/html4/">
  <h:tr>
    <h:td>Apples</h:td>
    <h:td>Bananas</h:td>
  </h:tr>
</h:table>

<f:table xmlns:f="https://www.w3schools.com/furniture">
  <f:name>African Coffee Table</f:name>
  <f:width>80</f:width>
  <f:length>120</f:length>
</f:table>

</root>'''
    ),
]
