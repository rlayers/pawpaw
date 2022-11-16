from __future__ import annotations
import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
import xml.etree.ElementTree as ET
import typing

import regex
from pawpaw import nuco, Ito
from pawpaw.errors import Errors
from pawpaw.arborform import Extract


# See 4 Qualified Names in https://www.w3.org/TR/xml-names/
class QualifiedName(typing.NamedTuple):
    prefix: Ito | None
    local_part: Ito

    @classmethod
    def from_src(cls, src: str | Ito) -> QualifiedName:
        if isinstance(src, str):
            src = Ito(src)
        elif not isinstance(src, Ito):
            raise Errors.parameter_invalid_type('src', src, str, Ito)
        
        parts = src.str_split(':', maxsplit=1)
        if len(parts) == 1:
            parts.insert(0, None)
        
        return cls(*parts)

    def __str__(self):
        start = self.prefix.start if self.prefix is not None else self.local_part.start
        stop = self.local_part.stop
        if (stop - start) == len(self.local_part.string):
            return self.local_part.string
        else:
            return self.local_part.string[start:stop]

# Deals with ElementTree.Element tag and attrib keys
class EtName(typing.NamedTuple):
    namespace: Ito | None
    name: Ito

    _re = regex.compile(r'(?P<namespace>\{.+?\})?(?P<name>.+)', regex.DOTALL)
    _extractor = Extract(_re)

    @classmethod
    def from_item(cls, item: str | Ito | ET.Element) -> EtName:
        if isinstance(item, str):
            item = Ito(item)
        elif isinstance(item, ET.Element):
            item = item.ito if hasattr(item, 'ito') else Ito(item.tag)
        elif not isinstance(item, Ito):
            raise Errors.parameter_invalid_type('item', item, str, Ito, ET.Element)

        vals = [*cls._extractor.traverse(item)]
        if len(vals) == 1:
            vals.insert(0, None)
        return cls(*vals)

    def __str__(self):
        start = self.namespace.start if self.namespace is not None else self.name.start
        stop = self.name.stop
        if (stop - start) == len(self.name.string):
            return self.name.string
        else:
            return self.name.string[start:stop]

class XmlHelper:
    @classmethod
    def get_element_text_if_found(cls, element: ET.Element, path: str) -> str | None:
        if not isinstance(element, ET.Element):
            raise Errors.parameter_invalid_type('element', element, ET.Element)

        if not isinstance(path, str):
            raise Errors.parameter_invalid_type('path', path, str)
                
        e = element.find(path)
        return None if e is None else e.text

    @classmethod
    def get_local_name(cls, item: str | ET.Element) -> str:
        if isinstance(item, str):
            tag = item
        elif isinstance(item, ET.element):
            tag = item.tag
        else:
            raise Errors.parameter_invalid_type('item', item, str, ET.Element)
        
        i = tag.find('}')
        return tag[i + 1:] if i >= 0 else tag
      
    @classmethod
    def get_namespace(cls, item: str | ET.Element) -> str | None:
        if isinstance(item, str):
            tag = item
        elif isinstance(item, ET.element):
            tag = item.tag
        else:
            raise Errors.parameter_invalid_type('item', item, str, ET.Element)
        
        i = tag.find('}')
        return tag[:i + 1] if i >= 0 else None

    @classmethod
    def get_default_namespace(cls, item: ET.ElementTree | ET.Element) -> str | None:
        if isinstance(item, ET.ElementTree):
            root = item.getroot()
        elif not isinstance(item, ET.Element):
            raise Errors.parameter_invalid_type('item',item, ET.ElementTree, ET.Element)

        while item.attrib.get('xmlns') is None and (parent := root.find('..')) is not None:
            root = parent

        return item.attrib.get('xmlns')
