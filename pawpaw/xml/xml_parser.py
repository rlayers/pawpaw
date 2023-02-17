import sys
# Force Python XML parser, not faster C version so that we can hook methods
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat

import regex
from pawpaw import Span, Ito, xml
from pawpaw.arborform import Extract

        
class XmlParser(ET.XMLParser):
    _NAMESPACE = r'(?P<' + xml.descriptors.NAMESPACE + r'>[^ :]+):'
    _NAME = r'(?P<' + xml.descriptors.NAME + r'>[^ />=]+)'
    _TAG = r'(?P<' + xml.descriptors.TAG + r'>(?:' + _NAMESPACE + r')?' + _NAME + r')'

    _VALUE = r'="(?P<' + xml.descriptors.VALUE + r'>[^"]+)"'
    _TAG_VALUE = _TAG + _VALUE

    _ATTRIBUTE = r'(?P<' + xml.descriptors.ATTRIBUTE + r'>' + _TAG_VALUE + r')'

    _itor_extract_tag = Extract(regex.compile(r'\<[\/\?]?' + _TAG, regex.DOTALL))
    _itor_extract_attributes = Extract(regex.compile(_ATTRIBUTE, regex.DOTALL))

    _PI = r'(?P<' + xml.descriptors.PI + r'>\<\?(?P<' + xml.descriptors.VALUE + r'>.*?)\?\>)'
    _COMMENT = r'(?P<' + xml.descriptors.COMMENT + r'>\<\!\-\-(?P<' + xml.descriptors.VALUE + r'>.*?)\-\-\>)'

    _itor_extract_pi_comments = Extract(regex.compile('|'.join((_PI, _COMMENT)), regex.DOTALL))

    class _Spans:
        line: Span | None = None
        column: Span | None = None
        byte: Span | None = None
        char: Span | None = None

    class _InternalIndexingParser:
        def __init__(self, text: str, encoding: str):
            self.text = text
            self.encoding = encoding
            self.bytes = text.encode(encoding)

            self.last_line_indexed: int | None = None
            self.last_line_char_offset: int | None = None
            self.last_line_byte_offset: int | None = None
            self.reset()

        def reset(self):
            self.last_line_indexed = 0
            self.last_line_char_offset = 0
            self.last_line_byte_offset = 0

        def char_offset_from(self, byte_offset: int) -> int:
            return len(self.bytes[0:byte_offset].decode(self.encoding))

        """
        Note : parser.CurrentColumnNumber is not well defined.  From official Python documentation:
        
            "Current columns number in the parser input"
            
       Assumption made here is that "column number" refers to chars, and may differ from bytes when unicode combining graphemes are encountered
        """
        def char_offset_from_ex(self, parser: ET.XMLParser) -> int:
            if self.last_line_indexed < parser.CurrentLineNumber:
                self.last_line_indexed = parser.CurrentLineNumber
                
                current_line_char_offset = self.last_line_char_offset + len(
                    self.bytes[self.last_line_byte_offset:parser.CurrentByteIndex].decode(
                        self.encoding)) - parser.CurrentColumnNumber
                current_line_byte_index = self.last_line_byte_offset + len(
                    self.text[self.last_line_char_offset:current_line_char_offset].encode(self.encoding))

                self.last_line_char_offset = current_line_char_offset
                self.last_line_byte_offset = current_line_byte_index

            rv = self.last_line_char_offset + parser.CurrentColumnNumber
            return rv

    def __init__(self, encoding: str = expat.native_encoding, ignore_empties: bool = True):
        super().__init__(encoding=encoding)
        self.encoding = encoding
        self.ignore_empties = ignore_empties
        self._indexing_parser: XmlParser._InternalIndexingParser | None = None

    def _start(self, *args, **kwargs) -> ET.Element:
        # Assume default XML parser (expat)
        rv = super()._start(*args, **kwargs)
        rv._spans = self._Spans()
        rv._spans.line = Span(self.parser.CurrentLineNumber, -1)
        rv._spans.column = Span(self.parser.CurrentColumnNumber, -1)
        rv._spans.byte = Span(self.parser.CurrentByteIndex, -1)
        rv._spans.char = Span(self._indexing_parser.char_offset_from_ex(self.parser), -1)
        return rv

    def _end(self, *args, **kwargs) -> ET.Element:
        # Assume default XML parser (expat)
        rv = super()._end(*args, **kwargs)
        rv._spans.line = Span(rv._spans.line.start, self.parser.CurrentLineNumber)
        rv._spans.column = Span(rv._spans.column.start, self.parser.CurrentColumnNumber)
        rv._spans.byte = Span(rv._spans.byte.start, self.parser.CurrentByteIndex)
        rv._spans.char = Span(rv._spans.char.start, self._indexing_parser.char_offset_from_ex(self.parser))
        return rv

    def feed(self, data) -> None:
        self._text = data
        self._indexing_parser = self._InternalIndexingParser(data, self.encoding)
        super().feed(data)

    text_comments = Extract

    def _find_text(self, start: int, stop: int) -> Ito | None:
        rv = Ito(self._text, start, stop, xml.descriptors.TEXT)
        if len(rv) > 0 and not (self.ignore_empties and rv.str_isspace()):
            rv.children.add(*self._itor_extract_pi_comments(rv))
            return rv

    def _extract_itos(self, element: ET.Element) -> None:
        start_tag = Ito(
            self._text,
            element._spans.char.start,
            self._text.index('>', element._spans.char.start + 1) + 1,
            xml.descriptors.START_TAG)
        
        start_tag.children.add(*self._itor_extract_tag(start_tag))

        attrs = [*self._itor_extract_attributes(start_tag)]
        if len(attrs) > 0:
            attrs_parent = Ito.join(*attrs, desc=xml.descriptors.ATTRIBUTES)
            attrs_parent.value_func = lambda ito: element.attrib
            attrs_parent.children.add(*attrs)
            start_tag.children.add(attrs_parent)

        for tag in start_tag.find_all('**[d:' + xml.descriptors.TAG + ']'):
            qn = xml.QualifiedName.from_src(tag)
            tag.value_func = lambda i: qn

        if (element._spans.char.stop + 2) < len(self._text) and self._text[element._spans.char.stop:element._spans.char.stop + 2] == '</':
            end_tag = Ito(
                self._text,
                element._spans.char.stop,
                self._text.index('>', element._spans.char.stop + 1) + 1,
                xml.descriptors.END_TAG)
            for c in self._itor_extract_tag(end_tag):
                c.value_func = lambda i: xml.QualifiedName.from_src(c)
                end_tag.children.add(c)
            end_index = end_tag.stop
        else:
            end_tag = None
            end_index = element._spans.char.stop

        ito = Ito(self._text, start_tag.start, end_index, xml.descriptors.ELEMENT)
        ito.value_func = lambda i: element

        ito.children.add(start_tag)
        
        # Note: Don't use element.text or element.tail here because these values:
        #   a) are absent for whitespace-only strs
        #   b) get html-decoded (to change entity references) and resulting offsets may not match original string
        #   c) could contain pi and comments
        # See https://docs.python.org/3/library/xml.etree.elementtree.html for definition of .text and .tail

        last_child: ET.Element | None = None
        for child in element:
            self._extract_itos(child)
            ito.children.add(child.ito)

            if last_child is not None:
                if (t := self._find_text(last_child.ito.stop, child.ito.start)) is not None:
                    ito.children.add(t)

            last_child = child

        if last_child is not None:
            if (t := self._find_text(last_child.ito.stop, end_tag.start)) is not None:
                ito.children.add(t)

        if end_tag is not None:
            stop = element[0].ito.start if len(element) > 0 else end_tag.start
            if (t := self._find_text(start_tag.stop, stop)) is not None:
                ito.children.add(t)

            ito.children.add(end_tag)

        element.ito = ito

    def close(self):
        rv = super().close()
        self._extract_itos(rv)
        return rv
