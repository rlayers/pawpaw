import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat

import regex
from segments import Span, Ito
from segments.itorator import Extract


class XmlStrings:
    NAME = r'(?P<Name>[^ />=]+)'
    VALUE = r'="(?P<Value>[^"]+)"'
    NAME_VALUE = NAME + VALUE

    NS_NAME = r'(?:(?P<Namespace>[^: ]+):)?' + NAME
    NS_NAME_VALUE = NS_NAME + VALUE


class XmlRegexes:
    ns_tag = regex.compile(r'\<(?P<Tag>' + XmlStrings.NS_NAME + r')', regex.DOTALL)
    attribute = regex.compile(r'(?P<Attribute>' + XmlStrings.NS_NAME_VALUE + r')', regex.DOTALL)


class XmlParser(ET.XMLParser):
    class _InternalIndexingParser:
        def __init__(self, text: str, encoding: str):
            self.text = text
            self.encoding = encoding
            self.bytes = text.encode(encoding)

            self.last_line_indexed: int | None = None
            self.last_line_byte_offset: int | None = None
            self.last_line_char_offset: int | None = None
            self.reset()

        def reset(self):
            self.last_line_indexed = 0
            self.last_line_byte_offset = 0
            self.last_line_char_offset = 0

        def char_offset_from(self, byte_offset: int) -> int:
            return len(self.bytes[0:byte_offset].decode(self.encoding))

        """
        Note : parser.CurrentColumnNumber is not well defined.  From official Python documentation:
        
            "Current columns number in the parser input"
            
       Assumption made here is that "column number" refers to chars, and may differ from bytes when unicode combining graphemes are encountered
        """
        def char_offset_from_ex(self, parser: ET.XMLParser) -> str:
            if self.last_line_indexed < parser.CurrentLineNumber:
                current_line_indexed = parser.CurrentLineNumber
                current_line_char_offset = self.last_line_char_offset + len(
                    self.bytes[self.last_line_byte_offset:parser.CurrentByteIndex].decode(
                        self.encoding)) - parser.CurrentColumnNumber
                current_line_byte_index = self.last_line_byte_offset + len(
                    self.text[self.last_line_char_offset:current_line_char_offset].encode(self.encoding))

                self.last_line_indexed = current_line_indexed
                self.last_line_byte_offset = current_line_byte_index
                self.last_line_char_offset = current_line_char_offset

            rv = self.last_line_char_offset + parser.CurrentColumnNumber
            return rv

    _tag_extractor = Extract(XmlRegexes.ns_tag)
    _attributes_extractor = Extract(XmlRegexes.attribute)

    def __init__(self, encoding: str = expat.native_encoding, ignore_empties: bool = True):
        super().__init__(encoding=encoding)
        self.encoding = encoding
        self.ignore_empties = ignore_empties
        self._indexing_parser: XmlParser._InternalIndexingParser | None = None

    def _start(self, *args, **kwargs) -> ET.Element:
        # Assume default XML parser (expat)
        element = super()._start(*args, **kwargs)
        element._start_line_number = self.parser.CurrentLineNumber
        element._start_column_number = self.parser.CurrentColumnNumber
        element._start_byte_index = self.parser.CurrentByteIndex
        element._start_char_index = self._indexing_parser.char_offset_from_ex(self.parser)
        return element

    def _end(self, *args, **kwargs) -> ET.Element:
        # Assume default XML parser (expat)
        element = super()._end(*args, **kwargs)
        element._end_line_number = self.parser.CurrentLineNumber
        element._end_column_number = self.parser.CurrentColumnNumber
        element._end_byte_index = self.parser.CurrentByteIndex
        element._end_char_index = self._indexing_parser.char_offset_from_ex(self.parser)
        return element

    def feed(self, data) -> None:
        self._text = data
        self._indexing_parser = self._InternalIndexingParser(data, self.encoding)
        super().feed(data)

    def _extract_itos(self, element: ET.Element):
        start_tag = Ito(self._text, element._start_char_index, self._text.index('>', element._start_char_index + 1) + 1, desc='Start_Tag')
        start_tag.children.add(*self._tag_extractor.traverse(start_tag))
        start_tag.children.add(*self._attributes_extractor.traverse(start_tag))

        if (element._end_char_index + 2) < len(self._text) and self._text[element._end_char_index:element._end_char_index + 2] == '</':
            end_tag = Ito(self._text, element._end_char_index, self._text.index('>', element._end_char_index + 1) + 1, desc='End_Tag')
            end_index = end_tag.stop
        else:
            end_tag = None
            end_index = element._end_char_index

        ito = Ito(self._text, start_tag.start, end_index, desc='Element')
        ito.value_func = lambda i: element

        ito.children.add(start_tag)
        if element.text is not None:
            if element.text is not None or not(self.ignore_empties and str.isspace(element.text)):
                text = Ito(self._text, start_tag.stop, start_tag.stop + len(element.text), desc='Text')
                ito.children.add(text)
            for child in element:
                self._extract_itos(child)
                ito.children.add(child.ito)
                if child.tail is not None:
                    if element.text is not None or not(self.ignore_empties and not str.isspace(element.tail)):
                        ito_text = Ito(self._text, child.ito.stop, child.ito.stop + len(child.tail), desc='Text')
                        ito.children.add(ito_text)
            if end_tag is not None:
                ito.children.add(end_tag)

        element.ito = ito

    def close(self):
        rv = super().close()
        self._extract_itos(rv)
        return rv
