# Using Pawpaw with ``nltk``

## Tokenization

### Convert nlkt tokenizer output to Ito

```python
>>> import nltk
>>> import pawpaw
>>> from pawpaw import Ito
>>> from nltk.tokenize import WhitespaceTokenizer
>>> s = 'The quick brown fox.'
>>> ws_tok = nltk.tokenize.WhitespaceTokenizer()
>>> tokens = [Ito(s, *span, 'token') for span in ws_tok.span_tokenize(s)]
>>> [str(i) for i in tokens]
['The', 'quick', 'brown', 'fox.']
```

### Use nltk tokenizer with split

```python
>>> import nltk
>>> import regex
>>> from pawpaw import Ito, arborform
>>> ws_tok = nltk.tokenize.WhitespaceTokenizer()
>>> splitter = arborform.Split(regex.compile(ws_tok._pattern, ws_tok._flags))
>>> i = Ito('The quick brown fox.')
>>> [str(i) for i in splitter.traverse(i)]
['The', 'quick', 'brown', 'fox.']
```

### Chaining NLP

```python
>>> from pawpaw import Ito, arborform
>>> s = 'Here is one sentence.  Here is another.'
>>> i = Ito(s)
>>>
>>> nltk_tok = nltk.tokenize
>>> sent_itor = pawpaw.arborform.Itorator.from_func(lambda ito: ito.from_substrings(ito, nltk_tok.sent_tokenize(str(ito))))
>>>
>>> word_itor = pawpaw.arborform.Itorator.from_func(lambda ito: ito.from_substrings(ito, nltk_tok.word_tokenize(str(ito))))
>>> sent_itor.itor_children = word_itor
>>>
>>> i.children.add(*sent_itor.traverse(i))
>>> vis_tree = pawpaw.visualization.pepo.Tree()
>>> print(vis_tree.dumps(i))
(0, 39) 'None' : 'Here is one sentence.  Here is another.'
├──(0, 21) 'None' : 'Here is one sentence.'
│  ├──(0, 4) 'None' : 'Here'
│  ├──(5, 7) 'None' : 'is'
│  ├──(8, 11) 'None' : 'one'
│  ├──(12, 20) 'None' : 'sentence'
│  └──(20, 21) 'None' : '.'
└──(23, 39) 'None' : 'Here is another.'
   ├──(23, 27) 'None' : 'Here'
   ├──(28, 30) 'None' : 'is'
   ├──(31, 38) 'None' : 'another'
   └──(38, 39) 'None' : '.'
```
