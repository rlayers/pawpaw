from .ontology import C_RULE, C_RULES, C_PATH, Discoveries, Ontology
del ontology

from ._query import OPERATORS, MUST_ESCAPE_CHARS, escape, descape, Query, compile, find_all, find
del _query