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
    _re = regex.compile(r'(?P<axis>(?P<order>[\+\-]?)(?P<key>\-|\.{1,4}|\*{1,3}|\<{1,3}|\>{1,3})(?P<or_self>[S]?))', regex.DOTALL)

    def __init__(self, phrase: segments.Types.C_ITO):
        m = phrase.regex_match(self._re)
        if m is None:
            raise ValueError(f'invalid phrase \'{phrase}\'')
        self.ito = next(phrase.from_match_ex(m))

        try:
            self.key = next(str(i) for i in self.ito.children if i.desc == 'key')
        except StopIteration:
            raise ValueError(f'phrase \'{phrase}\' missing axis key')

        self.order = next((str(i) for i in self.ito.children if i.desc == 'order'), None)
        
        self.or_self = next((str(i) for i in self.ito.children if i.desc == 'or_self'), None)
        
    def to_ecs(self, itos: segments.Types.C_IT_ITOS, final: segments.Types.C_ITO | None = None) -> segments.Types.C_IT_EITOS:
        e = -1
        for e, i in enumerate(itos):
            yield segments.Types.C_EITO(e, i)
        
        if e == -1 and self.or_self and final is not None:
            yield segments.Types.C_EITO(0, final)

    def find_all(self, itos: typing.Iterable[segments.Types.C_ITO]) -> segments.Types.C_IT_EITOS:
        reverse = (self.order is not None and str(self.order) == '-')

        if self.key == '....':
            for i in itos:
                root = i.parent
                if (root is not None):
                    while (next_par := root.parent) is not None:
                        root = next_par
                        
                if root is not None:
                    yield segments.Types.C_EITO(0, root)
                elif self.or_self:
                    yield segments.Types.C_EITO(0, i)

        elif self.key == '...':
            for i in itos:
                ancestors = []
                cur = i
                while (cur := cur.parent) is not None:
                    ancestors.append(cur)
                if len(ancestors) > 0:
                    if reverse:
                        ancestors.reverse()
                yield from self.to_ecs(ancestors, i)
                
        elif self.key == '..':
            for i in itos:
                if (p := i.parent) is not None:
                    yield segments.Types.C_EITO(0, p)
                elif self.or_self:
                    yield segments.Types.C_EITO(0, i)

        elif self.key == '.':
            yield from self.to_ecs(itos)  # Special case where each ito gets unique enumeration
            
            # TODO : raise exception if self.or_self?

        elif self.key == '-':
            rv = list(dict.fromkeys(itos))
            if reverse:
                rv.reverse()
            yield from self.to_ecs(rv)
            
            # TODO : raise exception if self.or_self?

        elif self.key == '*':
            for i in itos:
                step = -1 if reverse else 1
                yield from self.to_ecs(i.children[::step], i)

        elif self.key == '**':
            for i in itos:
                descendants = [*i.walk_descendants()]
                if reverse:
                    descendants.reverse()
                yield from self.to_ecs(descendants, i)

        elif self.key == '***':
            for i in itos:
                leaves = [*(d for d in i.walk_descendants() if len(d.children) == 0)]
                if reverse:
                    leaves.reverse()
                yield from self.to_ecs(leaves, i)
                
        elif self.key == '<<<':
            raise NotImplemented('Not yet...!')

        elif self.key == '<<':
            for i in itos:
                if (p := i.parent) is None:
                    sliced: List[segments.Types.C_ITO] = []
                else:
                    idx = p.children.index(i)
                    sliced = p.children[:idx]
                    if not reverse:
                        sliced.reverse()
                    
                yield from self.to_ecs(sliced, i)

        elif self.key == '<':
            for i in itos:
                if (p := i.parent) is None:
                    idx = -1
                else:
                    idx = p.children.index(i)
                    
                if idx > 0:
                    yield segments.Types.C_EITO(0, p.children[idx - 1])
                elif self.or_self:
                    yield segments.Types.C_EITO(0, i)

        elif self.key == '>':
            for i in itos:
                if (p := i.parent) is None:
                    idx = -1
                else:
                    idx = p.children.index(i)
                    
                if idx > -1 and idx < len(p.children) - 1:
                    yield segments.Types.C_EITO(0, p.children[idx + 1])
                elif self.or_self:
                    yield segments.Types.C_EITO(0, i)

        elif self.key == '>>':
            for i in itos:
                if (p := i.parent) is None:
                    sliced: List[segments.Types.C_ITO] = []
                else:
                    idx = p.children.index(i)
                    sliced = p.children[idx + 1:]
                    if reverse:
                        sliced.reverse()
                
                yield from self.to_ecs(sliced, i)

        elif self.key == '>>>':
            raise NotImplemented('Not yet...!')

        else:
            raise ValueError(f'invalid axis key \'{self.key}\'')


class Ecf(ABC):
    @classmethod
    def validate_values(cls, values: segments.Types.C_VALUES) -> segments.Types.C_VALUES:
        if values is None:
            raise ValueError('value expression found, however, no values dictionary supplied')
        return values
    
    @classmethod
    def validate_predicates(cls, predicates: segments.Types.C_PREDICATES) -> segments.Types.C_PREDICATES:
        if predicates is None:
            raise ValueError('predicate expression found, however, no predicates dictionary supplied')
        return predicates
    
    @abstractmethod
    def func(self, ec: segments.Types.C_EITO, values: segments.Types.C_VALUES, predicates: segments.Types.C_PREDICATES) -> bool:
        pass
    
    
class EcfTautology(Ecf):
    def func(self, ec: segments.Types.C_EITO, values: segments.Types.C_VALUES, predicates: segments.Types.C_PREDICATES) -> bool:
        return True
    

class EcfCombined(Ecf):
    _obs_pat_1 = r'(?<!\\)(?:(?:\\{2})*)'  # Odd number of backslashes ver 1
    _obs_pat_2 = r'\\(\\\\)*'  # Odd number of backslashes ver 2

    def __init__(
            self,
            ito: segments.Types.C_ITO,
            filters: typing.Sequence[F_EITO_V_P_2_B],
            operands: typing.Sequence[str]
    ):
        self.ito = ito
        
        if len(filters) == 0:
            raise ValueError(f'empty filters list')
        self.filters = filters

        if len(operands) != len(filters) - 1:
            raise ValueError(f'count of operands ({len(operands):,}) must be one less than count of filters ({len(filters):,}')
        self.operands = operands

    def func(self, ec: segments.Types.C_EITO, values: segments.Types.C_VALUES, predicates: segments.Types.C_PREDICATES) -> bool:
        acum = self.filters[0](ec, values, predicates)
        for f, o in zip(self.filters[1:], self.operands):
            op = OPERATORS.get(o)
            if op is None:
                raise ValueError('invalid operator \'{o}\'')
            cur = f(ec, values, predicates)
            acum = op(acum, cur)
        return acum


class EcfFilter(EcfCombined):
    _re_open_bracket = regex.compile(EcfCombined._obs_pat_1 + r'\[', regex.DOTALL)
    _re_close_bracket = regex.compile(EcfCombined._obs_pat_1 + r'\]', regex.DOTALL)

    _re = regex.compile(r'\[(?P<k>[a-z\-]+):\s*(?P<v>.+?)\]', regex.DOTALL)
    _re_balanced_splitter = regex.compile(
        r'(?P<bra>(?<!' + EcfCombined._obs_pat_2 + r')\[(?:(?:' + EcfCombined._obs_pat_2 + r'[\[\]]|[^\[\]])++|(?&bra))*(?<!' + EcfCombined._obs_pat_2 + r')\])',
        regex.DOTALL
    )

    @classmethod
    def _func(cls, key: str, value: str) -> F_EITO_V_P_2_B:
        if key in FILTER_KEYS['desc']:
            return lambda ec, values, predicates: ec.ito.desc in [descape(s) for s in segments.split_unescaped(value, ',')]

        if key in FILTER_KEYS['string']:
            return lambda ec, values, predicates: str(ec.ito) in [descape(s) for s in segments.split_unescaped(value, ',')]

        if key in FILTER_KEYS['string-casefold']:
            return lambda ec, values, predicates: str(ec.ito).casefold() in [
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

    def __init__(self, ito: segments.Types.C_ITO):
        filters: typing.List[F_EITO_V_P_2_B] = []
        operands: typing.List[str] = []

        if len([*ito.regex_finditer(self._re_open_bracket)]) != len([*ito.regex_finditer(self._re_close_bracket)]):
            raise ValueError(f'unbalanced brackets in filter(s) \'{ito}\'')
        last = None
        for f in ito.regex_finditer(self._re_balanced_splitter):
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
    _re_open_cur = regex.compile(EcfCombined._obs_pat_1 + r'\{', regex.DOTALL)
    _re_close_cur = regex.compile(EcfCombined._obs_pat_1 + r'\}', regex.DOTALL)

    _re = regex.compile(EcfFilter._obs_pat_1 + r'(?P<sq>\{.*)', regex.DOTALL)
    _re_balanced_splitter = regex.compile(
        r'(?P<cur>(?<!' + EcfCombined._obs_pat_2 + r')\{(?:(?:' + EcfCombined._obs_pat_2 + r'[{}]|[^{}])++|(?&cur))*(?<!' + EcfCombined._obs_pat_2 + r')\})',
        regex.DOTALL
    )
    
    @classmethod
    def _func(cls, sq: segments.Types.C_ITO) -> F_EITO_V_P_2_B:
        query = Query(sq)
        return lambda e, v, p: next(query.find_all(e.ito, v, p), None) is not None
    
    def __init__(self, ito: segments.Types.C_ITO):
        subqueries: typing.List[F_EITO_V_P_2_B] = []
        operands: typing.List[str] = []

        m = ito.regex_search(self._re)
        if m is None:
            raise ValueError(f'Invalid parameter \'subquery\' value: {ito}')

        s_q_g = m.group('sq')
        if len([*self._re_open_cur.finditer(s_q_g)]) != len([*self._re_close_cur.finditer(s_q_g)]):
            raise ValueError(f'unbalanced curly braces in sub-query(ies) \'{s_q_g}\'')
        sqs = [*self._re_balanced_splitter.finditer(s_q_g)]
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
    def __init__(self, phrase: segments.Types.C_ITO):
        self.ito = phrase
        self.axis = Axis(phrase)
        
        segments.Types.C_curl = next(segments.find_unescaped(phrase, '{', start=len(self.axis.ito)), phrase.stop)
        
        filt_ito = phrase[len(self.axis.ito):segments.Types.C_curl].str_strip()
        if len(filt_ito) == 0:
            self.filter = EcfTautology()
        else:
            self.filter = EcfFilter(filt_ito)

        sq_ito = phrase[segments.Types.C_curl:].str_strip()
        if len(sq_ito) == 0:
            self.subquery = EcfTautology()
        else:
            self.subquery = EcfSubquery(sq_ito)

    def combined(self, ec: segments.Types.C_EITO, values: segments.Types.C_VALUES, predicates: segments.Types.C_PREDICATES) -> bool:
        return self.filter.func(ec, values, predicates) and self.subquery.func(ec, values, predicates)

    def find_all(
            self,
            itos: segments.Types.C_IT_ITOS,
            values: segments.Types.C_VALUES,
            predicates: segments.Types.C_PREDICATES
    ) -> segments.Types.C_IT_ITOS:
        func = lambda ec: self.combined(ec, values, predicates)
        yield from (ec.ito for ec in filter(func, self.axis.find_all(itos)))


class Query:
    @classmethod
    def _split_phrases(cls, query: segments.Types.C_ITO) -> typing.Iterable[segments.Types.C_ITO]:
        ls = 0
        esc = False
        subquery_cnt = 0
        for i, ito in enumerate(query):
            c = str(ito)
            if esc:
                ls += 2
                esc = False
            elif c == '\\':
                esc = True
            elif c == '{':
                ls += 1
                subquery_cnt += 1
            elif c == '}':
                ls += 1
                subquery_cnt -= 1
            elif c == '/' and subquery_cnt == 0:
                yield query[i-ls:i]
                ls = 0
            else:
                ls += 1

        if esc:
            raise ValueError('found escape with no succeeding character in \'{query}\'')
        else:
            i += 1
            yield query[i-ls:i]

    def __init__(self, query: str | segments.Types.C_ITO):
        """Creates a compiled query that can be used to search an Ito hierarchy

        Args:
            query: one or more phrases, separated by foreslashes:

                query := {phrase}[/phrase][/phrase]...

                Each phrase consists of an axis, and optional order, filter, and subquery:

                phrase := {axis}[order][filter][subquery]

                An axis consists of one of the following operators:

                    AxisName ::= 'ancestor'
                                | 'ancestor-or-self'
                                | 'attribute'
                                | 'child'
                                | 'descendant'
                                | 'descendant-or-self'
                                | 'following'
                                | 'following-sibling'
                                | 'namespace'
                                | 'parent'
                                | 'preceding'
                                | 'preceding-sibling'
                                | 'self'

                See: https://www.w3.org/TR/1999/REC-xpath-19991116/

                https://docstore.mik.ua/orelly/xml/xslt/appb_03.htm

                https://www.tutorialspoint.com/xpath/xpath_axes.htm

        """
        if isinstance(query, str):
            query = segments.Ito(query)
            
        if not isinstance(query, segments.Ito):
            raise segments.Errors.parameter_invalid_type('query', query, str, segments.Types.C_ITO)
            
        if query is None or len(query) == 0 or not query.str_isprintable():
            raise segments.Errors.parameter_neither_none_nor_empty('query')

        self.phrases = [Phrase(p) for p in self._split_phrases(query)]

    def find_all(
            self,
            ito: segments.Types.C_ITO,
            values: segments.Types.C_VALUES = None,
            predicates: segments.Types.C_PREDICATES = None
    ) -> segments.Types.C_IT_ITOS:
        cur = [ito]
        for phrase in self.phrases:
            cur = phrase.find_all(cur, values, predicates)
        yield from cur
