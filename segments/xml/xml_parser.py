import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat

import regex
from segments import Span, Ito
from segments.floparse import Extract
import segments.xml.ito_descriptors as ITO_DESCRIPTORS

        
class XmlParser(ET.XMLParser):
    _NAME = r'(?P<' + ITO_DESCRIPTORS.NAME + r'>[^ />=]+)'
    _VALUE = r'="(?P<' + ITO_DESCRIPTORS.VALUE + r'>[^"]+)"'
    _NAME_VALUE = _NAME + _VALUE

    _NS_NAME = r'(?:(?P<' + ITO_DESCRIPTORS.NAMESPACE + r'>[^: ]+):)?' + _NAME
    _NS_NAME_VALUE = _NS_NAME + _VALUE

    _re_ns_tag = regex.compile(r'\<(?P<' + ITO_DESCRIPTORS.TAG + r'>' + _NS_NAME + r')', regex.DOTALL)
    _re_attribute = regex.compile(r'(?P<' + ITO_DESCRIPTORS.ATTRIBUTE + r'>' + _NS_NAME_VALUE + r')', regex.DOTALL)

    _itor_extract_tag = Extract(_re_ns_tag)
    _itor_extract_attributes = Extract(_re_attribute)

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

    def _extract_itos(self, element: ET.Element) -> None:
        start_tag = Ito(
            self._text,
            element._spans.char.start,
            self._text.index('>', element._spans.char.start + 1) + 1,
            ITO_DESCRIPTORS.START_TAG)
        start_tag.children.add(*self._itor_extract_tag.traverse(start_tag))
        start_tag.children.add(*self._itor_extract_attributes.traverse(start_tag))

        if (element._spans.char.stop + 2) < len(self._text) and self._text[element._spans.char.stop:element._spans.char.stop + 2] == '</':
            end_tag = Ito(
                self._text,
                element._spans.char.stop,
                self._text.index('>', element._spans.char.stop + 1) + 1,
                ITO_DESCRIPTORS.END_TAG)
            end_index = end_tag.stop
        else:
            end_tag = None
            end_index = element._spans.char.stop

        ito = Ito(self._text, start_tag.start, end_index, ITO_DESCRIPTORS.ELEMENT)
        ito.value_func = lambda i: element

        ito.children.add(start_tag)
        if element.text is not None:
            if element.text is not None or not(self.ignore_empties and str.isspace(element.text)):
                text = Ito(self._text, start_tag.stop, start_tag.stop + len(element.text), ITO_DESCRIPTORS.TEXT)
                ito.children.add(text)
            for child in element:
                self._extract_itos(child)
                ito.children.add(child.ito)
                if child.tail is not None:
                    if element.text is not None or not(self.ignore_empties and not str.isspace(element.tail)):
                        ito_text = Ito(self._text, child.ito.stop, child.ito.stop + len(child.tail), ITO_DESCRIPTORS.TEXT)
                        ito.children.add(ito_text)
            if end_tag is not None:
                ito.children.add(end_tag)

        element.ito = ito

    def close(self):
        rv = super().close()
        self._extract_itos(rv)
        return rv
