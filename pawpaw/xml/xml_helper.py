import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implementation (3.x hack)
import xml.etree.ElementTree as ET

import regex
from pawpaw import nuco
from pawpaw.errors import Errors


class XmlHelper:
  _re_default_ns = regex.compile(r'\{.+\}', regex.DOTALL)
  
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
        else
            raise Errors.parameter_invalid_type('item', item, str, ET.Element)
        
        i = tag.find('}')
        return tag[i + 1:] if i >= 0 else tag
      
    @classmethod
    def get_namespace(cls, item: str | ET.Element) -> str | None:
        if isinstance(item, str):
            tag = item
        elif isinstance(item, ET.element):
            tag = item.tag
        else
            raise Errors.parameter_invalid_type('item', item, str, ET.Element)
        
        i = tag.find('}')
        return tag[:i + 1] if i >= 0 else None

    @classmethod
    def get_default_namespace(cls, item: ET.ElementTree | ET.Element) -> str | None:
        if isinstance(item, ET.ElementTree):
          root = item.getroot()
        elif isinstance(item, ET.Element):
          root = item
          while (parent := root.find('..')) is not None:
              root = parent
        else:
            raise Errors.parameter_invalid_type('item',item, ET.ElementTree, ET.Element)
          
        return cls.get_namespace(root)

      
      
