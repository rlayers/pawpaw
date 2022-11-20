==========================
Using Pawpaw with ``nltk``
==========================

************
Tokenization
************

Convert nlkt tokenizer output to Ito
====================================

>>> import nltk
>>> import pawpaw
>>> from pawpaw import Ito
>>> from nltk.tokenize import WhitespaceTokenizer
>>> s = 'The quick brown fox.'
>>> ws_tok = nltk.tokenize.WhitespaceTokenizer()
>>> tokens = [Ito(s, *span, 'token') for span in ws_tok.span_tokenize(s)]
>>> [str(i) for i in tokens]
['The', 'quick', 'brown', 'fox.']

Use nltk tokenizer with split
=============================

>>> import nltk
>>> import regex
>>> import pawpaw
>>> ws_tok = nltk.tokenize.WhitespaceTokenizer()
>>> splitter = pawpaw.arborform.Split(regex.compile(ws_tok._pattern, ws_tok._flags))
>>> i = pawpaw.Ito('The quick brown fox.')
>>> [str(i) for i in splitter.traverse(i)]
['The', 'quick', 'brown', 'fox.']

Chaining NLP
============

>>> from pawpaw import Ito
>>> s = 'Here is one sentence.  Here is another.'
>>> i = Ito(s)
>>>
>>> nltk_tok = nltk.tokenize
>>> sent_itor = pawpaw.arborform.Wrap(lambda ito: ito.from_substrings(ito, *nltk_tok.sent_tokenize(str(ito))))
>>>
>>> word_itor = pawpaw.arborform.Wrap(lambda ito: ito.from_substrings(ito, *nltk_tok.word_tokenize(str(ito))))
>>> sent_itor.itor_children = word_itor
>>>
>>> i.children.add(*(sent_itor.traverse(i)))
>>> dumper = pawpaw.visualization.Compact()
>>> print(dumper.dumps(i))
exit(0)