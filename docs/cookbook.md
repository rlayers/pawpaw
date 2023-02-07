# Pawpaw Cookbook

## Extraction

### Extract all characters as ``Ito``

```python
>>> s = ' abc '
>>> i = Ito(s, 1, -1)
>>> [*i]
[Ito(' abc ', 1, 2, None), Ito(' abc ', 2, 3, None), Ito(' abc ', 3, 4, None)]
```

### Extract all characters as ``str`` 

```python
>>> from pawpaw import Ito
>>> s = 'abc'
>>> print(*s)  # For a str, you would do this
a b c
>>> i = Ito(s)  # For an ito, you can...
>>> print(*(str(j) for j in i))  # do this (create str tuple)...
a b c
>>> print(*(str(i)))  # or this (convert to str and unpack)...
a b c
>>> print(*i)  # or even this (send itos to print, which performs str() on each item)
a b c
```

### Add all characters as child ``Ito``

```python
>>> from pawpaw import Ito
>>> s = ' abc '
>>> i = Ito(s, 1, -1)
>>> i.children.add(*i)
>>> [*i.children]
[Ito(' abc ', 1, 2, None), Ito(' abc ', 2, 3, None), Ito(' abc ', 3, 4, None)]
```

### Create a char-extracting ``Itorator``

```python
>>> from pawpaw import Ito, arborform
>>> char_itor = arborform.Itorator.wrap(lambda ito: iter(ito))  # 1. If you don't need a desc
>>> char_itor = arborform.Itorator.wrap(lambda ito: Ito.from_substrings(s, *ito, desc='char'))  # 2. If you need a desc
```

### Perform NLP Extraction
```python
>>> import requests
>>> import pawpaw
>>>
>>> sleepy_hollow = 'https://www.gutenberg.org/ebooks/41.txt.utf-8'
>>> with requests.get(sleepy_hollow) as r:
>>>     root = pawpaw.nlp.SimpleNlp().from_text(r.text)
>>> para = root.children[0]
>>> print(pawpaw.visualization.pepo.Tree().dumps(para))
(1, 81) 'Paragraph' : 'The Project Gutenber…y Washington Irving'
└──(1, 81) 'Sentence' : 'The Project Gutenber…y Washington Irving'
   ├──(1, 4) 'Word' : 'The'
   ├──(5, 12) 'Word' : 'Project'
   ├──(13, 22) 'Word' : 'Gutenberg'
   ├──(23, 28) 'Word' : 'eBook'
   ├──(29, 31) 'Word' : 'of'
   ├──(32, 35) 'Word' : 'The'
   ├──(36, 42) 'Word' : 'Legend'
   ├──(43, 45) 'Word' : 'of'
   ├──(46, 52) 'Word' : 'Sleepy'
   ├──(53, 59) 'Word' : 'Hollow'
   ├──(61, 63) 'Word' : 'by'
   ├──(64, 74) 'Word' : 'Washington'
   └──(75, 81) 'Word' : 'Irving'
```

## XML

### Get spans for elements:

**Code:**

```python
import sys
sys.modules['_elementtree'] is None
import xml.etree.ElementTree as ET
from pawpaw import xml
text = """<?xml version="1.0"?>
<data>
    <country name="Liechtenstein">
        <rank updated="yes">2</rank>
        <year>2008</year>
        <gdppc>141100</gdppc>
        <neighbor name="Austria" direction="E"/>
        <neighbor name="Switzerland" direction="W"/>
    </country>
</data>"""
root = ET.fromstring(text, parser=xml.XmlParser())
for e in root.find('.//'):
    print(f'{e.tag}: {e.ito:%span}')
```

**Output:**

```python
rank: (72, 100)
year: (109, 126)
gdppc: (135, 156)
neighbor: (165, 205)
neighbor: (214, 258)
```

### Get spans for element text:

```python
import sys
sys.modules['_elementtree'] is None
import xml.etree.ElementTree as ET
from pawpaw import xml
text = """<doc xmlns:w="https://example.com">
    <w:r>
        <w:rPr>
            <w:sz w:val="36"/>
            <w:szCs w:val="36"/>
        </w:rPr>
        <w:t>BIG_TEXT</w:t>
    </w:r>
</doc>"""
root = ET.fromstring(text, parser=xml.XmlParser())
prefix_map = xml.XmlHelper.get_prefix_map(root)
e = root.find('.//w:t', namespaces=prefix_map)
ito = e.ito.find('**[d:text]')
print(f'{ito:%span}')
```

**Output:**

```python
(156, 164)
```