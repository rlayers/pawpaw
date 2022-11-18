from __future__ import annotations
import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
import typing

import regex
from pawpaw import Ito, Types
from pawpaw.errors import Errors
from pawpaw.arborform import Extract
from pawpaw.xml import ito_descriptors
import pawpaw

# See 4 Qualified Names in https://www.w3.org/TR/xml-names/
class QualifiedName(typing.NamedTuple):
    prefix: Types.C_ITO | None
    local_part: Types.C_ITO

    @classmethod
    def from_src(cls, src: str | Types.C_ITO) -> QualifiedName:
        if isinstance(src, str):
            src = Ito(src)
        elif not isinstance(src, Ito):
            raise Errors.parameter_invalid_type('src', src, str, Types.C_ITO)
        
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

# # Deals with ElementTree.Element tag and attrib keys
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
    def get_qualified_name(cls, ito: Types.C_ITO) -> QualifiedName:
        if not isinstance(ito, Ito):
            raise Errors.parameter_invalid_type('ito', ito, Types.C_ITO)
        elif ito.desc not in (ito_descriptors.START_TAG, ito_descriptors.ATTRIBUTE):
            raise ValueError(f'parameter \'{ito}\' lacks children with descriptor \'{ito_descriptors.NAME}\' - did you forget to use pawpaw.XmlParser?')

        ns = ito.find(f'*[d:{ito_descriptors.NAMESPACE}]')
        name = ito.find(f'*[d:{ito_descriptors.NAME}]')

        return QualifiedName(ns, name)

    _query_xmlns = pawpaw.query.compile(f'*[d:{ito_descriptors.START_TAG}]/*[d:{ito_descriptors.ATTRIBUTE}]' + '{*[s:xmlns]}')

    @classmethod
    def get_xmlns(cls, element: ET.Element) -> typing.Dict[QualifiedName, Types.C_ITO]:
        if not isinstance(element, ET.Element):
            raise Errors.parameter_invalid_type('element', element, ET.Element)
        elif not hasattr(element, 'ito'):
            raise ValueError(f'parameter \'{element}\' missing attr \'.ito\' - did you forget to use pawpaw.XmlParser?')
        
        rv: typing.Dict[QualifiedName, str] = {}
        
        for xmlns in cls._query_xmlns.find_all(element.ito):
            qn = cls.get_qualified_name(xmlns)
            value = xmlns.find(f'*[d:{ito_descriptors.VALUE}]')
            rv[qn] = value

        return rv

    @classmethod
    def get_prefix_map(cls, element: ET.ElementTree) -> typing.Dict[str, str]:
        """Builds a prefix dict suitable for passing to ET methods such as Element.find('foo:goo', prefix_map);
        keys & values are suitable for passing to xml.etree.ElementTree.register_namespace

        Args:
            element: ET.Element

        Raises:
            Errors.parameter_invalid_type
            ValueError
        """
        return {str(qn.local_part): str(val) for qn, val in cls.get_xmlns(element).items() if qn.prefix is not None}

    @classmethod
    def get_default_namespace(cls, element: ET.ElementTree) -> Types.C_ITO | None:
        return next((val for qn, val in cls.get_xmlns(element).items() if qn.prefix is None), None)

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