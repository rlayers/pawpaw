from __future__ import annotations
from abc import ABC, abstractmethod
import collections.abc
import operator
import typing

import regex
import segments


OPERATORS = {
    '&': operator.and_,
    '|': operator.or_,
    '^': operator.xor
}

FILTER_KEYS = {
    'desc': {'desc', 'd'},
    'string': {'string', 's'},
    'string-casefold': {'string-casefold', 'scf', 'lcs'},
    'index': {'index', 'i'},
    'predicate': {'predicate', 'p'},
    'value': {'value', 'v'}
}

MUST_ESCAPE_CHARS = ('\\', '[', ']', '/', ',', '{', '}',)


class EC(typing.NamedTuple):
    index: int
    ito: segments.Types.C


C_IT_EC = typing.Iterable[EC]
C_VALUES = typing.Dict[str, typing.Any] | None
C_PREDICATES = typing.Dict[str, typing.Callable[[EC], bool]] | None
F_EC_V_P_2_B = typing.Callable[[EC, C_VALUES, C_PREDICATES], bool]


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


class Axis:
    _re = regex.compile(r'(?P<axis>(?P<key>\-|\.{1,4}|\*{1,3}|\<{1,2}|\>{1,2})\s*(?P<order>[nr]?))', regex.DOTALL)

    def __init__(self, phrase: segments.Types.C):
        m = phrase.regex_match(self._re)
        if m is None:
            raise ValueError(f'invalid phrase \'{phrase}\'')
        self.ito = next(phrase.from_match_ex(m))

        try:
            self.key = next(i.__str__() for i in self.ito.children if i.desc == 'key')
        except StopIteration:
            raise ValueError(f'phrase \'{phrase.__str__()}\' missing axis key')

        self.order = next((i.__str__() for i in self.ito.children if i.desc == 'order'), None)

    @classmethod
    def to_ecs(cls, itos: segments.Types.C_IT_ITOS) -> C_IT_EC:
        yield from (EC(e, i) for e, i in enumerate(itos))

    def find_all(self, itos: typing.Iterable[segments.Types.C]) -> C_IT_EC:
        reverse = (self.order is not None and self.order.__str__() == 'r')

        if self.key == '....':
            for i in itos:
                if (r := i.get_root()) is not None:
                    yield EC(0, r)

        elif self.key == '...':
            for ito in itos:
                ancestors = []
                cur = ito
                while (cur := cur.parent) is not None:
                    ancestors.append(cur)
                if reverse:
                    ancestors.reverse()
                yield from self.to_ecs(ancestors)

        elif self.key == '..':
            for i in itos:
                if (p := i.parent) is not None:
                    yield EC(0, p)

        elif self.key == '.':
            yield from self.to_ecs(itos)  # Special case where each ito gets unique enumeration

        elif self.key == '-':
            rv = list(collections.OrderedDict.fromkeys(itos))
            if reverse:
                rv.reverse()
            yield from self.to_ecs(rv)

        elif self.key == '*':
            for i in itos:
                if reverse:
                    yield from self.to_ecs(i.children[::-1])
                else:
                    yield from self.to_ecs(i.children)

        elif self.key == '**':
            for i in itos:
                if reverse:
                    yield from self.to_ecs([*i.walk_descendants()][::-1])
                else:
                    yield from self.to_ecs([*i.walk_descendants()])

        elif self.key == '***':
            for i in itos:
                if reverse:
                    yield from self.to_ecs([*(d for d in i.walk_descendants() if len(d.children) == 0)][::-1])
                else:
                    yield from self.to_ecs([*(d for d in i.walk_descendants() if len(d.children) == 0)])

        elif self.key == '<<':
            for i in itos:
                if (p := i.parent) is not None:
                    sliced = p.children[0:p.children.index(i)]
                    if reverse:
                        sliced.reverse()
                    yield from self.to_ecs(sliced)

        elif self.key == '<':
            for i in itos:
                if (p := i.parent) is not None:
                    idx = p.children.index(i)
                    if idx > 0:
                        yield EC(0, p.children[idx - 1])

        elif self.key == '>':
            for i in itos:
                if (p := i.parent) is not None:
                    idx = p.children.index(i)
                    if idx < len(p.children) - 1:
                        yield EC(0, p.children[idx + 1])

        elif self.key == '>>':
            for i in itos:
                if (p := i.parent) is not None:
                    sliced = p.children[p.children.index(i) + 1:]
                    if reverse:
                        sliced.reverse()
                    yield from self.to_ecs(sliced)

        else:
            raise ValueError(f'invalid axis key \'{self.key}\'')


class Ecf(ABC):
    @classmethod
    def validate_values(cls, values: C_VALUES) -> C_VALUES:
        if values is None:
            raise ValueError('value expression found, however, no values dictionary supplied')
        return values
    
    @classmethod
    def validate_predicates(cls, predicates: C_PREDICATES) -> C_PREDICATES:
        if predicates is None:
            raise Miss ValueError('predicate expression found, however, no predicates dictionary supplied')
        return predicates
    
    @abstractmethod
    def func(self, ec: EC, values: C_VALUES, predicates: C_PREDICATES) -> bool:
        pass
    
    
class EcfTautology(Ecf):
    def func(self, ec: EC, values: C_VALUES, predicates: C_PREDICATES) -> bool:
        return True
    

class EcfCombined(Ecf):
    _obs_pat_1 = r'(?<!\\)(?:(?:\\{2})*)'  # Odd number of backslashes ver 1
    _obs_pat_2 = r'\\(\\\\)*'  # Odd number of backslashes ver 2

    def __init__(self, ito: segments.Types.C, filters: typing.Sequence[F_EC_V_P_2_B], operands: typing.Sequence[str]):
        self.ito = ito
        
        if len(filters) == 0:
            raise ValueError(f'empty filters list')
        self.filters = filters

        if len(operands) != len(filters) - 1:
            raise ValueError(f'count of operands ({len(operands):,}) must be one less than count of filters ({len(filters):,}')
        self.operands = operands

    def func(self, ec: EC, values: C_VALUES, predicates: C_PREDICATES) -> bool:
        acum = self.filters[0](ec, values, predicates)
        for f, o in zip(self.filters[1:], self.operands):
            op = OPERATORS.get(o)
            if op is None:
                raise ValueError('invalid operator \'{o}\'')
            cur = f(ec, values, predicates)
            acum = op(acum, cur)
        return acum


class EcfFilter(EcfCombined):
    _open_bracket = regex.compile(EcfCombined._obs_pat_1 + r'\[', regex.DOTALL)
    _close_bracket = regex.compile(EcfCombined._obs_pat_1 + r'\]', regex.DOTALL)

    _re = regex.compile(r'\[(?P<k>[a-z\-]+):\s*(?P<v>.+?)\]', regex.DOTALL)
    _balanced_splitter = regex.compile(
        r'(?P<bra>(?<!' + EcfCombined._obs_pat_2 + r')\[(?:(?:' + EcfCombined._obs_pat_2 + r'[\[\]]|[^\[\]])++|(?&bra))*(?<!' + EcfCombined._obs_pat_2 + r')\])',
        regex.DOTALL
    )

    @classmethod
    def _func(cls, key: str, value: str) -> F_EC_V_P_2_B:
        if key in FILTER_KEYS['desc']:
            return lambda ec, values, predicates: ec.ito.desc in [descape(s) for s in segments.split_unescaped(value, ',')]

        if key in FILTER_KEYS['string']:
            return lambda ec, values, predicates: ec.ito.__str__() in [descape(s) for s in segments.split_unescaped(value, ',')]

        if key in FILTER_KEYS['string-casefold']:
            return lambda ec, values, predicates: ec.ito.__str__().casefold() in [
                descape(s).casefold() for s in segments.split_unescaped(value.casefold(), ',')
            ]

        if key in FILTER_KEYS['index']:
            ints: typing.Set[int] = set()
            for i_chunk in value.split(','):
                try:
                    _is = [int(i.strip()) for i in i_chunk.split('-')]
                except ValueError:
                    raise ValueError(f'invalid integer in \'value\'')

                len_is = len(_is)
                if len_is == 1:
                    ints.add(_is[0])
                elif len_is == 2:
                    for i in range(*_is):
                        ints.add(i)
                else:
                    raise ValueError('invalid index item \'value\'')

            return lambda ec, values, predicates: ec.index in ints

        if key in FILTER_KEYS['predicate']:
            keys = [descape(s) for s in segments.split_unescaped(value, ',')]
            return lambda ec, values, predicates: any(p(ec) for p in [v for k, v in cls.validate_predicates(predicates).items() if k in keys])

        if key in FILTER_KEYS['value']:
            keys = [descape(s) for s in segments.split_unescaped(value, ',')]
            return lambda ec, values, predicates: ec.ito.value() in [v for k, v in cls.validate_values(values).items() if k in keys]

        raise ValueError(f'unknown filter key \'{key}\'')

    def __init__(self, ito: segments.Types.C):
        filters: typing.List[F_EC_V_P_2_B] = []
        operands: typing.List[str] = []

        if len([*ito.regex_finditer(self._open_bracket)]) != len([*ito.regex_finditer(self._close_bracket)]):
            raise ValueError(f'unbalanced brackets in filter(s) \'{ito}\'')
        last = None
        for f in ito.regex_finditer(self._balanced_splitter):
            if last is not None:
                start = last.span(0)[1]
                stop = f.span(0)[0]
                op = ito.string[start:stop].strip()
                if len(op) == 0:
                    raise ValueError(
                        f'missing operator between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
                elif op not in OPERATORS.keys():
                    raise ValueError(
                        f'invalid filter operator \'{op}\' between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
                operands.append(op)
            m = self._re.fullmatch(f.group(0))
            if m is None:
                raise ValueError(f'invalid filter \'{f.group(0)}\'')
            filters.append(self._func(m.group('k'), m.group('v')))
            last = f

        super().__init__(ito, filters, operands)


class EcfSubquery(EcfCombined):
    _open_cur = regex.compile(EcfCombined._obs_pat_1 + r'\{', regex.DOTALL)
    _close_cur = regex.compile(EcfCombined._obs_pat_1 + r'\}', regex.DOTALL)

    _re = regex.compile(_obs_pat_1 + r'(?P<sq>\{.*)', regex.DOTALL)
    _balanced_splitter = regex.compile(
        r'(?P<cur>(?<!' + EcfCombined._obs_pat_2 + r')\{(?:(?:' + EcfCombined._obs_pat_2 + r'[{}]|[^{}])++|(?&cur))*(?<!' + EcfCombined._obs_pat_2 + r')\})',
        regex.DOTALL
    )
    
    @classmethod
    def _func(cls, sq: segments.Types.C) -> F_EC_V_P_2_B:
        query = Query(sq)
        return lambda e, v, p: next(query.find_all(e.ito, v, p), None) is not None
    
    def __init__(self, ito: segments.Types.C):
        subqueries: typing.List[F_EC_V_P_2_B] = []
        operands: typing.List[str] = []

        m = ito.regex_search(self._re)
        if m is None:
            raise ValueError(f'Invalid parameter \'subquery\' value: {ito}')

        s_q_g = m.group('sq')
        if len([*self._open_cur.finditer(s_q_g)]) != len([*self._close_cur.finditer(s_q_g)]):
            raise ValueError(f'unbalanced curly braces in sub-query(ies) \'{s_q_g}\'')
        sqs = [*self._balanced_splitter.finditer(s_q_g)]
        last = None
        for sq in sqs:
            if last is not None:
                start = last.span(0)[1]
                stop = sq.span(0)[0]
                op = s_q_g[start:stop].strip()
                if len(op) == 0:
                    raise ValueError(
                        f'missing operator between subqueries \'{last.group(0)}\' and \'{sq.group(0)}\'')
                elif op not in OPERATORS.keys():
                    raise ValueError(
                        f'invalid subquery operator \'{op}\' between subqueries \'{last.group(0)}\' and \'{sq.group(0)}\'')
            subqueries.append(self._func(segments.Ito.from_match(sq, 0)[1:-1]))
            last = sq
            
        super().__init__(ito, subqueries, operands)

        
class Phrase:
    def __init__(self, phrase: segments.Types.C):
        self.ito = phrase
        self.axis = Axis(phrase)
        
        unesc_curl = next(segments.find_unescaped(phrase, '{', start=len(self.axis.ito)), phrase.stop)
        
        filt_ito = phrase[len(self.axis.ito):unesc_curl].str_strip()
        if len(filt_ito) == 0:
            self.filter = EcfTautology()
        else:
            self.filter = EcfFilter(filt_ito)

        sq_ito = phrase[unesc_curl:].str_strip()
        if len(sq_ito) == 0:
            self.subquery = EcfTautology()
        else:
            self.subquery = EcfSubquery(sq_ito)

    def combined(self, ec: EC, values: C_VALUES, predicates: C_PREDICATES) -> bool:
        return self.filter.func(ec, values, predicates) and self.subquery.func(ec, values, predicates)

    def find_all(self, itos: segments.Types.C_IT_ITOS, values: C_VALUES, predicates: C_PREDICATES) -> segments.Types.C_IT_ITOS:
        func = lambda ec: self.combined(ec, values, predicates)
        yield from (ec.ito for ec in filter(func, self.axis.find_all(itos)))


class Query:
    @classmethod
    def _split_phrases(cls, query: segments.Types.C) -> typing.Iterable[segments.Types.C]:
        query = query.__str__()  # TODO - get rid of this
        rv = ''
        escape = False
        subquery_cnt = 0
        for i, c in enumerate(query):
            if escape:
                rv += f'\\{c}'
                escape = False
            elif c == '\\':
                escape = True
            elif c == '{':
                rv += c
                subquery_cnt += 1
            elif c == '}':
                rv += c
                subquery_cnt -= 1
            elif c == '/' and subquery_cnt == 0:
                yield segments.Ito(query, i - len(rv), i)
                rv = ''
            else:
                rv += c

        if escape:
            raise ValueError('found escape with no succeeding character in \'{query}\'')
        else:
            i += 1
            yield segments.Ito(query, i - len(rv), i)

    def __init__(self, query: str | segments.Types.C):
        if isinstance(query, str):
            query = segments.Ito(query)
            
        if not isinstance(query, segments.Ito):
            raise segments.Errors.parameter_invalid_type('query', query, str, segments.Types.C)
            
        if query is None or len(query) == 0 or not query.str_isprintable():
            raise segments.Errors.parameter_neither_none_nor_empty('query')

        self.phrases = [Phrase(p) for p in self._split_phrases(query)]

    def find_all(self, ito: segments.Types.C, values: C_VALUES = None, predicates: C_PREDICATES = None) -> segments.Types.C_IT_ITOS:
        cur = [ito]
        for phrase in self.phrases:
            cur = phrase.find_all(cur, values, predicates)
        yield from cur
