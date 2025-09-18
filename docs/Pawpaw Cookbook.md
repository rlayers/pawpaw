# Pawpaw Cookbook

## Extraction

### Extract all characters as ``Ito``

```python
>>> s = ' abc '
>>> i = Ito(s, 1, -1)
>>> [*i]
[Ito(span=(1, 2), desc='', substr='a'), Ito(span=(2, 3), desc='', substr='b'), Ito(span=(3, 4), desc='', substr='c')]

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
[Ito(span=(1, 2), desc='', substr='a'), Ito(span=(2, 3), desc='', substr='b'), Ito(span=(3, 4), desc='', substr='c')]
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

### Extract children and then extract a second set of children based on the leftover space:

#### **Technique 1:** Use ``Split`` with ``BoundaryRetention.ALL``:

**Code:**

```python
from pawpaw import Ito, arborform, visualization
import regex

s = 'It measures 10 <!--inches--> long <!--front to back-->'

itor_self = arborform.Reflect()

pat = r"""
(?<comment>\<\!\-\-
    (?<value>.*?)
\-\-\>)
"""
re = regex.compile(pat, regex.VERBOSE | regex.DOTALL)
itor_comment = arborform.Split(arborform.Extract(re), boundary_retention=arborform.Split.BoundaryRetention.ALL)
con = arborform.Connectors.Children.Add(itor_comment)
itor_self.connections.append(con)

re = regex.compile(r'(?<token>\S+)', regex.DOTALL)
itor_token = arborform.Extract(re)
con = arborform.Connectors.Delegate(itor_token, lambda ito: ito.desc is None)
itor_comment.connections.append(con)

ito = Ito(s, desc='phrase')
v_tree = visualization.pepo.Tree()
print(v_tree.dumps(next(itor_self(ito))))
```

**Output:**

```
(0, 54) 'phrase' : 'It measures 10 <!--i…!--front to back-->'
├──(0, 2) 'token' : 'It'
├──(3, 11) 'token' : 'measures'
├──(12, 14) 'token' : '10'
├──(15, 28) 'comment' : '<!--inches-->'
│  └──(19, 25) 'value' : 'inches'
├──(29, 33) 'token' : 'long'
└──(34, 54) 'comment' : '<!--front to back-->'
   └──(38, 51) 'value' : 'front to back'
```

#### **Technique 2**: Using ``Ito.from_gaps``:

**Code:**

```python
from pawpaw import Ito, arborform, visualization
import regex

s = 'It measures 10 <!--inches--> long <!--front to back-->'

itor_self = arborform.Reflect()

pat = r"""
(?<comment>\<\!\-\-
    (?<value>.*?)
\-\-\>)
"""
re = regex.compile(pat, regex.VERBOSE | regex.DOTALL)
itor_comment = arborform.Extract(re)
con = arborform.Connectors.Children.Add(itor_comment)
itor_self.connections.append(con)

itor_invert_children = arborform.Itorator.wrap(lambda ito: Ito.from_gaps(ito, ito.children, return_zero_widths=False))
con = arborform.Connectors.Children.Add(itor_invert_children)
itor_self.connections.append(con)

re = regex.compile(r'(?<token>\S+)', regex.DOTALL)
itor_token = arborform.Extract(re)
con = arborform.Connectors.Delegate(itor_token)
itor_invert_children.connections.append(con)

ito = Ito(s, desc='phrase')
v_tree = visualization.pepo.Tree()
print(v_tree.dumps(next(itor_self(ito))))
```

**Output:**

```python
(0, 54) 'phrase' : 'It measures 10 <!--i…!--front to back-->'
├──(0, 2) 'token' : 'It'
├──(3, 11) 'token' : 'measures'
├──(12, 14) 'token' : '10'
├──(15, 28) 'comment' : '<!--inches-->'
│  └──(19, 25) 'value' : 'inches'
├──(29, 33) 'token' : 'long'
└──(34, 54) 'comment' : '<!--front to back-->'
   └──(38, 51) 'value' : 'front to back'
```

### Create an itorator to strip whitespace

**Code:**

```python
import pawpaw

ito = pawpaw.Ito('ABC def   ')  # Basis str has trailing whitespace
print(f'Input: "{ito}"')

itor = pawpaw.arborform.Itorator.wrap(
   lambda ito: (ito.str_rstrip(),)  # Passed func must return sequence
)
print(f'Output: "{next(itor(ito))}"')

```

**Output:**

```python
Input: "ABC def   "
Output: "ABC def"
```

### Build a recursive parser

Because itorator chains are linked via ``Connection`` objects, the same ``Itorator`` can be used multiple times in a chain:

**Code:**

```python
import regex
from pawpaw import Ito, find_balanced, arborform, visualization

itor = arborform.Reflect()
itor.connections.append(arborform.Connectors.Recurse(arborform.Desc('expression')))

itor_entities = arborform.Itorator.wrap(lambda ito: find_balanced(ito, '(', ')'))
itor_entities.connections.append(arborform.Connectors.Recurse(arborform.Desc('subexpression')))

itor_split = arborform.Split(itor_entities, boundary_retention=arborform.Split.BoundaryRetention.ALL, desc='expression')

itor_trim_parens = arborform.Itorator.wrap(lambda ito: (Ito(ito, 1, -1, ito.desc),))
itor_split.connections.append(arborform.Connectors.Recurse(itor_trim_parens, lambda ito: ito.desc == 'subexpression'))

# Add itor to its own itorator chain
itor_split.connections.append(arborform.Connectors.Recurse(itor, lambda ito: ito.desc == 'subexpression'))

itor.connections.append(arborform.Connectors.Children.Add(itor_split, lambda ito: ito.str_find('(') > -1))

v_tree = visualization.pepo.Tree()
s = 'a + (b + (c * d) / (g * h))'
i = Ito(s)
print(v_tree.dumps(next(itor(i))))

```

**Output:**

```python
(0, 27) 'expression' : 'a + (b + (c * d) / (g * h))'
├──(0, 4) 'expression' : 'a +'
└──(5, 26) 'expression' : 'b + (c * d) / (g * h)'
   ├──(5, 9) 'expression' : 'b + '
   ├──(10, 15) 'expression' : 'c * d'
   ├──(16, 19) 'expression' : ' / '
│  └──(20, 25) 'expression' : 'g * h'
```

## XML

### Get spans for elements:

**Code:**

```python
import sys
sys.modules['_elementtree'] = None
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
sys.modules['_elementtree'] = None
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
