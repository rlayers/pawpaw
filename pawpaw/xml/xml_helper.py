from __future__ import annotations
import sys
# Force Python XML parser, not faster C version so that we can hook methods
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
import typing

import regex
from pawpaw import Ito, query, xml
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

        vals = [*cls._extractor(item)]
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


class XmlErrors:
    @classmethod
    def element_lacks_ito_attr(cls, name: str, value: typing.Any) -> ValueError:
        return ValueError(f'parameter \'{name}\' missing attr \'.ito\' - did you forget to use pawpaw.xml.XmlParser?')

    @classmethod
    def ito_value_not_element(cls, name: str, value: typing.Any) -> ValueError:
        return ValueError(f'parameter \'{name}\' has a .value() that is not instance of xml.etree.ElementTree.Element - did you forget to use pawpaw.xml.XmlParser?')

class XmlHelper:
    @classmethod
    def get_qualified_name(cls, ito: Ito) -> QualifiedName:
        if not isinstance(ito, Ito):
            raise Errors.parameter_invalid_type('ito', ito, Ito)
        elif ito.desc not in (xml.descriptors.START_TAG, xml.descriptors.ATTRIBUTE):
            raise ValueError(f'parameter \'{ito}\' lacks children with descriptor \'{xml.descriptors.NAME}\' - did you forget to use pawpaw.xml.XmlParser?')

        ns = ito.find(f'**[d:{xml.descriptors.NAMESPACE}]')
        name = ito.find(f'**[d:{xml.descriptors.NAME}]')

        return QualifiedName(ns, name)

    _re_xmlns = regex.compile(r'xmlns(?:\:.+)?', regex.DOTALL)
    _query_xmlns_predicates = {'is_xmlns': lambda ei: ei.ito.regex_fullmatch(XmlHelper._re_xmlns) is not None}
    __query_xmlns: query.Query = None

    # Lazily instantiate to avoid some circular dependencies
    @classmethod
    @property
    def _query_xmlns(cls) -> query.Query:
        if cls.__query_xmlns is None:
            cls.__query_xmlns = query.compile(f'*[d:{xml.descriptors.START_TAG}]/*[d:{xml.descriptors.ATTRIBUTES}]/*[d:{xml.descriptors.ATTRIBUTE}]' + '{*[p:is_xmlns]}')

        return cls.__query_xmlns

    @classmethod
    def get_xmlns(cls, element: ET.Element) -> typing.Dict[QualifiedName, Ito]:
        if cls._query_xmlns is None:
            cls.__query_xmlns = query.compile(f'*[d:{xml.descriptors.START_TAG}]/*[d:{xml.descriptors.ATTRIBUTES}]/*[d:{xml.descriptors.ATTRIBUTE}]' + '{*[p:is_xmlns]}')

        if not isinstance(element, ET.Element):
            raise Errors.parameter_invalid_type('element', element, ET.Element)
        elif not hasattr(element, 'ito'):
            raise XmlErrors.element_lacks_ito_attr('element', element)
        
        return {
            cls.get_qualified_name(xmlns): xmlns.find(f'*[d:{xml.descriptors.VALUE}]')
            for xmlns
            in cls.__query_xmlns.find_all(element.ito, predicates=cls._query_xmlns_predicates)
        }

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
    def get_default_namespace(cls, element: ET.ElementTree) -> str | None:
        while element is not None:
            rv = next((val for qn, val in cls.get_xmlns(element).items() if qn.prefix is None), None)
            if rv is not None:
                return f'{{{rv}}}'
            element = cls.get_parent_element(element)

        return None

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
        elif isinstance(item, ET.Element):
            tag = item.tag
        else:
            raise Errors.parameter_invalid_type('item', item, str, ET.Element)
        
        i = tag.find('}')
        return tag[i + 1:] if i >= 0 else tag
      
    @classmethod
    def get_namespace(cls, item: str | ET.Element) -> str | None:
        if isinstance(item, str):
            tag = item
        elif isinstance(item, ET.Element):
            tag = item.tag
        else:
            raise Errors.parameter_invalid_type('item', item, str, ET.Element)
        
        i = tag.find('}')
        return tag[:i + 1] if i >= 0 else None

    @classmethod
    def find_all_descendants_by_local_name(cls, element: ET.Element, local_name: str) -> typing.Iterable[ET.Element]:
        if not isinstance(element, ET.Element):
            raise Errors.parameter_invalid_type('element', element, ET.Element)

        if not isinstance(local_name, str):
            raise Errors.parameter_invalid_type('local_name', local_name, str)

        for e in element.findall('.//'):
            if local_name == cls.get_local_name(e):
                yield e

    @classmethod
    def find_descendant_by_local_name(cls, element: ET.Element, local_name: str) -> ET.Element | None:
        return next(cls.find_all_descendants_by_local_name(element, local_name), None)

    @classmethod
    def get_text_itos(cls, element: ET.ElementTree) -> typing.Iterable[Ito]:
        yield from element.ito.find_all(f'*[d:{xml.descriptors.TEXT}]')

    @classmethod
    def get_parent_element(cls, element: ET.Element) -> ET.Element | None:
        if not isinstance(element, ET.Element):
            raise Errors.parameter_invalid_type('element', element, ET.Element)
        elif not hasattr(element, 'ito'):
            raise XmlErrors.element_lacks_ito_attr('element', element)

        if (ito := element.ito.find(f'...[d:{xml.descriptors.ELEMENT}]')) is not None:
            return ito.value()

        return None

    @classmethod
    def reverse_find(cls, element: ET.Element, predicate: str) -> ET.Element | None:
        """ElementTree support for XPATH is limited, and the '..' operator will
        not traverse upwards beyond the node you issued a .find or .find_all with.
        This method applies an XPATH predicate to the current node, and returns if
        it passes.  If it fails, it uses the .ito to traverse UP to the parent,
        and repeates the process.

        Args:
            element: _description_
            predicate: _description_

        Raises:
            Errors.parameter_invalid_type: _description_
            XmlErrors.element_lacks_ito_attr: _description_
            Errors.parameter_invalid_type: _description_

        Returns:
            Matching element or None
        """
        
        if not isinstance(element, ET.Element):
            raise Errors.parameter_invalid_type('element', element, ET.Element)
        elif not hasattr(element, 'ito'):
            raise XmlErrors.element_lacks_ito_attr('element', element)

        if not isinstance(predicate, str):
            raise Errors.parameter_invalid_type('predicate', predicate, str)

        while element is not None:
            if element.find(f'.[{predicate}]') is not None:
                return element

            element = cls.get_parent_element(element)

        return element
