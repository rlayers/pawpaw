# Pawpaw Cookbook

## Extraction

### Extract all characters as ``str`` 

```python
>>> s = 'abc'
>>> print(*s)  # For a str, you would do this
a b c
>>> print(*(str(i)))  # So do this for an Ito
a b c
```

### Extract all characters as ``Ito``

```python
>>> s = ' abc '
>>> i = Ito(s, 1, -1)
>>> [*i]
[Ito(' abc ', 1, 2, None), Ito(' abc ', 2, 3, None), Ito(' abc ', 3, 4, None)]
```

### Add all characters as child ``Ito``

```python
>>> s = ' abc '
>>> i = Ito(s, 1, -1)
>>> i.children.add(*i)
>>> [*i.children]
[Ito(' abc ', 1, 2, None), Ito(' abc ', 2, 3, None), Ito(' abc ', 3, 4, None)]
```

### Create a char-extracting ``Itorator``

```python
>>> char_itor = Itorator.wrap(lambda ito: iter(ito))  # 1. If you don't need a desc
>>> char_itor = Itorator.wrap(lambda ito: Ito.from_substrings(s, *ito, desc='char'))  # 2. If you need a desc
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
(1, 81) 'Paragraph' : 'The Project Gutenberg eBook of The Leg…
└──(1, 81) 'Sentence' : 'The Project Gutenberg eBook of The Leg…
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
