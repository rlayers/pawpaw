from __future__ import annotations
import operator

from pawpaw import Ito, Errors, Types, arborform, find_balanced
from pawpaw.ontology import Ontology, Discoveries
import regex


# Ordered by precedance
OPERATORS = {
    '!': operator.not_,
    '&': operator.and_,
    '^': operator.xor,
    '|': operator.or_,
}

MUST_ESCAPE_CHARS = ('\\', '[',)

def escape(value: str) -> str:
    rv = value.replace('\\', '\\\\')  # Must do backslash before other chars
    for c in filter(lambda e: e != '\\',  MUST_ESCAPE_CHARS):
        rv = rv.replace(c, f'\\{c}')
    return rv

def descape(value: str) -> str:
    rv = ''
    esc = False
    for c in value:
        if esc or c != '\\':
            rv += c
            esc = False
        else:
            esc = True

    if esc:
        raise ValueError(f'found escape with no succeeding character in \'value\'')

    return rv

class Query():
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
        pat_xor = r'(?P<op_xor>\^)'
        pat_or = r'(?P<op_or>\|)'
        pat_entity = r'(?P<entity>[a-z\d_]+)'
        pat_quantifier = r'(?P<op_quantifier>\{(?P<qty_min>\d+)?(?:,(?P<qty_max>\d+)?)?\}|(?P<qty_symbol>[?*+]))'
        itor_residual = arborform.Split(
            arborform.Extract(regex.compile('|'.join([pat_not, pat_and, pat_xor, pat_or, pat_entity, pat_quantifier]), regex.DOTALL | regex.IGNORECASE)),
            boundary_retention=arborform.Split.BoundaryRetention.ALL
        )
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(itor_residual, None))

        filter_empties = arborform.Filter(lambda ito: ito.desc is not None)
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(filter_empties))

        rv.connections.append(arborform.Connectors.Children.Add(itor_child_placeholder))
        return rv
    
    _itor = _build_itor()

    @classmethod
    def __init__(self, src: str | Ito) -> Ito:
        if not isinstance(src, (str, Ito)):
            raise Errors.parameter_invalid_type('src', src, str, Ito)

        src = Ito(src, desc='query')
        if len(src) == 0:
            raise ValueError(f'parameter ''src'' is empty')
        
        rv = [*self._itor(src)]
        if len(rv) != 1:
            raise ValueError(f'parse error')
        
        self._parse = rv[0]
    
    def find_all(
        self,
        ontology: Ontology,
        src: str | Ito
    ) -> Types.C_IT_ITOS:
        raise NotImplemented()

    def find(
        self,
        ontology: Ontology,
        src: str | Ito
    ) -> Ito | None:
        return next(self.find_all(ontology, src), None)


def compile(path: Types.C_QPATH) -> Query:
    return Query(path)

def find_all(
        query: str | Ito,
        ontology: Ontology,
        src: str | Ito
) -> Types.C_IT_ITOS:
    yield from Query(query).find_all(ontology, src)

def find(
        query: str | Ito,
        ontology: Ontology,
        src: str | Ito
) -> Ito | None:
    return next(find_all(query, ontology, src), None)
