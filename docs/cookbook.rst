========================
``ito-segment`` Cookbook
========================

**********
Extraction
**********

Extract all ``char`` as ``str`` 
=================================================

::

 s = 'abc'

 print(*Ito(s))

Extract all ``char`` as ``Itos``
=============================================

::

 s = 'abc'
 
 print(*[Ito(s, i, i + 1) for i, c in enumerate(s)])  # Painful...

 print(*Ito.from_substrings(s, *s))  # better...