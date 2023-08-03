import sys
sys.modules['_elementtree'] = None
import xml.etree.ElementTree as ET

from pawpaw import xml


# Setup HTML tabs
x = "<span>"
x_ = "</span>"

# Set recursion depth to 255
depth = 300

xml_text = f'{x * depth}<p>text to be extracted</p >{x_ * depth}'

root = ET.fromstring(xml_text, parser=xml.XmlParser())
node = root.ito.find('**[d:element]{*[d:start_tag]/**[d:name]&[s:p]}/*[d:text]')
print(str(node))

