========================
``ito-segment`` Cookbook
========================

**********
Extraction
**********

Extract all characters as ``str`` 
=================================================

::

 >>> s = 'abc'
 >>> print(*s)  # For a str, you would do this
 a b c
 >>> print(*(str(i)))  # So do this for an Ito
 a b c

Extract all characters as ``Itos``
=============================================

::

 >>> s = ' abc '
 >>> i = Ito(s, 1, -1)
 >>> [*i]
 [Ito(' abc ', 1, 2, None), Ito(' abc ', 2, 3, None), Ito(' abc ', 3, 4, None)]

Add all characters as child ``Itos``
====================================

::

 >>> s = ' abc '
 >>> i = Ito(s, 1, -1)
 >>> i.children.add(*i)
 >>> [*i.children]
 [Ito(' abc ', 1, 2, None), Ito(' abc ', 2, 3, None), Ito(' abc ', 3, 4, None)]


Create a char-extracting itorator
=================================

::

 >>> chars = Wrap(lambda ito: iter(ito))  # Use pawpaw.itorator.Wrap
 >>> chars = Wrap(lambda ito: Ito.from_substrings(s, *ito, desc='char'))  # If you want to supply a desc
 