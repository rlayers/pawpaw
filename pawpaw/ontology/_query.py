from __future__ import annotations
from abc import ABC, abstractmethod
import dataclasses
import operator
import typing

from pawpaw import Span, Ito, Errors, Types, arborform, find_balanced, split_unescaped
from pawpaw.ontology import Ontology, Discoveries
import regex


# Ordered by precedance
OPERATORS = {
    '!': operator.not_,
    '&': operator.and_,
    '^': operator.xor,
    '|': operator.or_,
}

MUST_ESCAPE_CHARS = ('\\', ']', '.')

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

@dataclasses.dataclass
class _StackFrame:
    discoveries: Discoveries
    start: int
    stop: int
    op_stack: list[_Op] = dataclasses.field(default_factory=list)

class _Op(ABC):
    @abstractmethod
    def __call__(self, stack_frame: _StackFrame) -> typing.Iterable[Types.C_IT_ITOS]:
        pass

class _Entity(_Op):
    def __init__(self, entity: Ito):
        self._entity = entity

    def __call__(self, stack_frame: _StackFrame) -> typing.Iterable[Types.C_IT_ITOS]:
        discovery = stack_frame.discoveries
        for path_step in split_unescaped(self._entity, '.'):
            discovery = discovery[str(path_step)]
        if id(discovery) == id(stack_frame.discoveries):
            raise Exception(f'discoveries missing entity \'{str(self._entity)}\'')
        
        yield tuple(
            filter(
                lambda ito: stack_frame.start <= ito.start and ito.stop <= stack_frame.stop,
                discovery.walk()
            )
        )


class _Mul(_Op):
    def __call__(self, stack_frame: _StackFrame) -> Types.C_IT_ITOS:
        it1, it2 = stack_frame.op_stack[-2:]
        sf1 = _StackFrame(stack_frame.discoveries, stack_frame.start, stack_frame.stop, stack_frame.op_stack[:-2])
        for i1 in next(it1(sf1)):
            sf2 = _StackFrame(stack_frame.discoveries, i1.stop, stack_frame.stop, stack_frame.op_stack[:-2])
            for i2 in next(it2(sf2)):
                yield [i1, i2]


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
        pat_entity = r'(?P<entity>[a-z\d_\.]+)'
        pat_quantifier = r'(?P<op_quantifier>\{(?P<qty_min>\d+)?(?:,(?P<qty_max>\d+)?)?\}|(?P<qty_symbol>[?*+]))'
        itor_residual = arborform.Split(
            arborform.Extract(regex.compile('|'.join([pat_not, pat_and, pat_xor, pat_or, pat_entity, pat_quantifier]), regex.DOTALL | regex.IGNORECASE)),
            boundary_retention=arborform.Split.BoundaryRetention.ALL
        )
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(itor_residual, None))

        filter_empties = arborform.Filter(lambda ito: ito.desc is not None)
        itor_child_placeholder.connections.append(arborform.Connectors.Recurse(filter_empties))

        itor_entity_split = arborform.Itorator.wrap(lambda ito: (s[0].clone(),) if len(s := [*split_unescaped(ito, '.')]) == 1 and id(s[0]) == id(ito) else s)
        itor_entity_split.connections.append(arborform.Connectors.Delegate(arborform.Desc('path_step')))
        itor_child_placeholder.connections.append(arborform.Connectors.Children.Add(itor_entity_split, 'entity'))

        rv.connections.append(arborform.Connectors.Children.Add(itor_child_placeholder))
        return rv
    
    _itor = _build_itor()

    # Ordered low to high
    _OPERATOR_PRECEDENCES = [['op_xor', 'op_or'], ['op_and'], ['op_not', 'op_quantifier'], ['query', 'LPAREN', 'RPAREN']]

    @classmethod
    def _get_precedence(cls, token: Ito) -> int | None:
        for i, sublst in enumerate(cls._OPERATOR_PRECEDENCES):
            if token.desc in sublst:
                return i
        return

    @classmethod
    def _shunting_yard(cls, expression: Types.C_IT_ITOS):
        output_queue = []
        operator_stack = []
        
        for token in expression:
            token_p = cls._get_precedence(token)
            if token_p is None:
                output_queue.append(token)

            elif token.desc == 'LPAREN':
                operator_stack.append(token)

            elif token.desc == 'RPAREN':
                while operator_stack[-1] != 'LPAREN':
                    output_queue.append(operator_stack.pop())
                operator_stack.pop()

            elif token.desc == 'query':
                output_queue.extend(cls._shunting_yard(token.children))

            else:
                if len(operator_stack) == 0:
                    op_stack_p = None
                else:
                    op_stack_p = cls._get_precedence(operator_stack[-1])
                while len(operator_stack) and op_stack_p is not None and token_p <= op_stack_p:
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)

        while operator_stack:
            output_queue.append(operator_stack.pop())

        return output_queue

    @classmethod
    def __init__(self, src: str | Ito) -> Ito:
        if not isinstance(src, (str, Ito)):
            raise Errors.parameter_invalid_type('src', src, str, Ito)

        src = Ito(src, desc='query')
        if len(src) == 0:
            raise ValueError(f'parameter ''src'' is empty')
        
        rv = [*self._itor(src)]
        if len(rv) != 1:
            raise ValueError(f'parse error...')
        
        if len(rv[0].children) == 0:
            raise ValueError(f'parse error...')
        
        self._parse = self._shunting_yard(rv[0].children)
        
        for i in self._parse:
            print(f'{i:%substr: %desc}')

        exit(0)
    
    def find_all(
        self,
        discoveries: Discoveries,
        src: str | Ito
    ) -> Types.C_IT_ITOS:
        
        if isinstance(src, str):
            src = Ito(src)

        start, stop = src.span
        stack = []

        raise NotImplemented()

    def find(
        self,
        discoveries: Discoveries,
        src: str | Ito
    ) -> Ito | None:
        return next(self.find_all(discoveries, src), None)


def compile(path: Types.C_QPATH) -> Query:
    return Query(path)

def find_all(
        query: str | Ito,
        discoveries: Discoveries,
        src: str | Ito
) -> Types.C_IT_ITOS:
    yield from Query(query).find_all(discoveries, src)

def find(
        query: str | Ito,
        discoveries: Discoveries,
        src: str | Ito
) -> Ito | None:
    return next(find_all(query, discoveries, src), None)
