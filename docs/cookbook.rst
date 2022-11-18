========================
``ito-segment`` Cookbook
========================

**********
Extraction
**********

Extract all characters as ``str`` 
=================================================

::

 s = 'abc'
 print(*s)  # For a str, do this

 i = Ito(s)
 print(*str(Ito))  # For an Ito, do this
 
Extract all characters as ``Itos``
=============================================

::

 s = 'abc'
 print(*Ito(s))


 Create a char-extracting itorator
=============================================

::

 chars = Wrap(lambda ito: iter(ito))  # Use pawpaw.itorator.Wrap

 chars = Wrap(lambda ito: Ito.from_substrings(s, *ito, desc='char'))  # If you want to also supply a desc
 