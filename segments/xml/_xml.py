import sys
# Force Python XML parser, not faster C accelerators because we can't hook the C implemntation (3.x hack)
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat

import regex
from segments.ito import Span, Ito

class XmlStrings:
  pass

class XmlRegexes:
  pass

class XmlParser:
  pass
