from __future__ import annotations
import dataclasses
import json
import typing

from pawpaw import Ito, Types, Errors, arborform, find_balanced
from pawpaw.arborform import Itorator
import regex

C_RULE = Itorator | Types.F_ITO_2_IT_ITOS
C_RULES = dict[str, C_RULE]
C_PATH = typing.Sequence[str]

class Discoveries(dict):
    def __init__(self, *args, **kwargs):
        self._itos: list[Ito] = list(kwargs.pop('itos', tuple()))
        dict.__init__(self, *args, **kwargs )

    @property
    def itos(self) -> list[Ito]:
        return self._itos   
    
    def __str__(self):
        c = ', '.join(f'{k}: {str(v)}' for k, v in self.items())
        return f'{{itos: {[str(i) for i in self._itos]}, {c}}}'
    
    def _flatten(self, filter_empties: bool = True, path: C_PATH = tuple()) -> dict[C_PATH, list[Ito]]:
        rv = {} if len(self.itos) == 0 and filter_empties else {tuple(path): self.itos}
        for key in self.keys():
            rv |= self[key]._flatten(filter_empties, path + (key,))
        return rv

    def flatten(self, filter_empties: bool = True) -> dict[C_PATH, list[Ito]]:
        return self._flatten(filter_empties, )
    
class Ontology(dict):
    def __missing__(self, key):
        if isinstance(key, typing.Sequence) and (lk := len(key)) > 0 and not isinstance(key, str):
            rv = self[key[0]]
            if lk > 1:
                rv = rv[key[1:]]
            return rv
        else:
            raise KeyError(key)

    def __init__(self, *args, **kwargs):
        self._rules: list[C_RULE] = kwargs.pop('rules', [])
        dict.__init__(self, *args, **kwargs )

    @property
    def rules(self) -> list[C_RULE]:
        return self._rules

    def __str__(self):
        c = ', '.join(f'{k}: {str(v)}' for k, v in self.items())
        return f'{{rules: {self._rules}, {c}}}'   
    
    def discover(self, *itos: Ito) -> Discoveries:
        rv = Discoveries()

        for rule in self._rules:
            for i in itos:
                rv.itos.extend(rule(i))

        for k, v in self.items():
            rv[k] = v.discover(*itos)

        return rv

class Query():

    mathematical_white_square_brackets = {
        'LEFT': '\u27E6',   # ⟦
        'RIGHT': '\u27E7',  # ⟧
    }

    @staticmethod
    def _build_itor() -> arborform.Itorator:
        rv = arborform.Reflect()
        rv.connections.append(arborform.Connectors.Recurse(arborform.Desc('query')))

        itor_child_placeholder = arborform.Reflect() 

        itor_entities = arborform.Itorator.wrap(lambda ito: find_balanced(ito, '[', ']'))
        itor_entities.connections.append(arborform.Connectors.Delegate(arborform.Desc('entity')))
        itor_split_brackets = arborform.Split(itor_entities, boundary_retention=arborform.Split.BoundaryRetention.ALL)
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(itor_split_brackets))
        
        itor_trim_brackets = arborform.Itorator.wrap(lambda ito: (Ito(ito, 1, -1, ito.desc),))
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(itor_trim_brackets, 'entity'))

        itor_sqs = arborform.Itorator.wrap(lambda ito: find_balanced(ito, '(', ')'))
        itor_sqs.connections.append(arborform.Connectors.Delegate(arborform.Desc('subquery')))
        itor_split_sqs = arborform.Split(itor_sqs, boundary_retention=arborform.Split.BoundaryRetention.ALL)
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(itor_split_sqs, None))

        itor_trim_parens = arborform.Itorator.wrap(lambda ito: (Ito(ito, 1, -1, ito.desc),))
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(itor_trim_parens, 'subquery'))

        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(rv, 'subquery'))
                                            
        pat_not = r'(?P<op_not>!*)'
        pat_and = r'(?P<op_and>&)'
        pat_or = r'(?P<op_or>\|)'
        pat_entity = r'(?P<entity>[a-z\d_]+)'
        pat_quantifier = r'(?P<op_quantifier>\{(?P<qty_min>\d+)?(?:,(?P<qty_max>\d+)?)?\}|(?P<qty_symbol>[?*+]))'
        itor_residual = arborform.Split(
            arborform.Extract(regex.compile('|'.join([pat_not, pat_and, pat_or, pat_entity, pat_quantifier]), regex.DOTALL | regex.IGNORECASE)),
            boundary_retention=arborform.Split.BoundaryRetention.ALL
        )
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(itor_residual, None))

        filter_empties = arborform.Filter(lambda ito: ito.desc is not None)
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(filter_empties))

        rv.connections.append(arborform.Connectors.Children.Add(itor_child_placeholder))
        return rv
    
    _itor = _build_itor()

    @classmethod
    def parse(cls, src: str | Ito) -> Ito:
        if not isinstance(src, (str, Ito)):
            raise Errors.parameter_invalid_type('src', src, str, Ito)

        src = Ito(src, desc='query')
        if len(src) == 0:
            raise ValueError(f'parameter ''src'' is empty')
        
        rv = [*cls._itor(src)]
        if len(rv) != 1:
            raise ValueError(f'parse error')
        
        return rv[0]

    def __init__(self, path: Types.C_QPATH):
        if isinstance(path, str):
            path = pawpaw.Ito(path)
        elif not isinstance(path, pawpaw.Ito):
            raise pawpaw.Errors.parameter_invalid_type('path', path, pawpaw.Types.C_QPATH)

        self._lbound = mathematical_white_square_brackets['LEFT']
        self._rbound = mathematical_white_square_brackets['RIGHT']

        self._re = regex.compile(_pat, regex.DOTALL | regex.VERBOSE)
        self._chain: list[term]