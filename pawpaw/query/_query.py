from __future__ import annotations
from abc import ABC, abstractmethod
import itertools
import operator
import typing

import regex
import pawpaw


# Ordered by precedance
OPERATORS = {
    '~': operator.not_,
    '&': operator.and_,
    '^': operator.xor,
    '|': operator.or_,
}

FILTER_KEYS = {
    'desc': {'desc', 'd'},
    'str': {'string', 's'},
    'str-casefold': {'str-casefold', 'scf', 'lcs'},
    'str-casefold-ew': {'str-casefold-ew', 'scfew', 'lcsew'},
    'str-casefold-sw': {'str-casefold-sw', 'scfsw', 'lcssw'},
    'str-ew': {'str-ew', 'sew'},
    'str-sw': {'str-sw', 'ssw'},
    'index': {'index', 'i'},
    'predicate': {'predicate', 'p'},
    'value': {'value', 'v'}
}

MUST_ESCAPE_CHARS = ('\\', '[', ']', '/', ',', '{', '}',)


class QueryErrors:
    @classmethod
    def unbalanced_parentheses(
            cls,
            expression: pawpaw.Ito | str,
            sub_region: pawpaw.Ito | str | int = None) -> ValueError:
        msg = f'unbalanced parentheses in \'{expression}\''
        if isinstance(sub_region, int):
            msg += f' at location {sub_region}'
        elif isinstance(sub_region, (pawpaw.Ito, str)):
            msg += f' in sub-region \'{sub_region}\''
        return ValueError(msg)

    @classmethod
    def empty_parentheses(
            cls,
            expression: pawpaw.Ito | str,
            sub_region: pawpaw.Ito | str | int = None) -> ValueError:
        msg = f'empty parentheses in \'{expression}\''
        if isinstance(sub_region, int):
            msg += f' at location {sub_region}'
        elif isinstance(sub_region, (pawpaw.Ito, str)):
            msg += f' in sub-region \'{sub_region}\''
        return ValueError(msg)


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
    _re = regex.compile(r'(?P<order>[\+\-]?)(?P<key>\.{1,4}|\*{1,3}|\>\<|\<{1,3}|\>{1,3})(?P<or_self>(?:\!{1,2})?)', regex.DOTALL)

    def __init__(self, phrase: pawpaw.Ito):
        m = phrase.regex_match(self._re)
        if m is None:
            raise ValueError(f'invalid phrase \'{phrase}\'')
        self.ito = phrase.from_match(m)[0]

        try:
            self.key = next(str(i) for i in self.ito.children if i.desc == 'key')
        except StopIteration:
            raise ValueError(f'phrase \'{phrase}\' missing axis key')

        self.order = next((str(i) for i in self.ito.children if i.desc == 'order'), None)
        
        self.or_self = next((str(i) for i in self.ito.children if i.desc == 'or_self'), None)
        
    @property
    def reverse(self) -> bool:
        return self.order is not None and str(self.order) == '-'

    def to_ecs(
        self,
        itos: pawpaw.Types.C_IT_ITOS,
        or_self_ito: pawpaw.Ito | None = None
    ) -> pawpaw.Types.C_IT_EITOS:
        _iter = iter(itos)
        stopped = False
        e = 0

        if self.or_self == '!!' and or_self_ito is not None and not self.reverse:
            try:
                first = next(_iter)
            except StopIteration:
                stopped = True

            if not stopped:
                yield pawpaw.Types.C_EITO(e, or_self_ito)
                e += 1
                
                if first is not or_self_ito:
                    yield pawpaw.Types.C_EITO(e, first)
                    e += 1
                
        last = None
        if not stopped:
            for i in _iter:
                yield pawpaw.Types.C_EITO(e, i)
                e += 1

        if e == 0:
            if self.or_self and or_self_ito is not None:
                yield pawpaw.Types.C_EITO(e, or_self_ito)

        elif self.or_self == '!!' and or_self_ito is not None and self.reverse:
            yield pawpaw.Types.C_EITO(e, or_self_ito)

    def find_all(self, itos: typing.Iterable[pawpaw.Ito]) -> pawpaw.Types.C_IT_EITOS:
        reverse = (self.order is not None and str(self.order) == '-')

        if self.key == '....':
            for i in itos:
                root = i.parent
                if (root is not None):
                    while (next_par := root.parent) is not None:
                        root = next_par
                        
                yield from self.to_ecs([] if root is None else [root], i)

        elif self.key == '...':
            for i in itos:
                ancestors = []
                cur = i
                while (cur := cur.parent) is not None:
                    ancestors.append(cur)
                if reverse:
                    yield from self.to_ecs(reversed(ancestors), i)
                else:
                    yield from self.to_ecs(ancestors, i)
                
        elif self.key == '..':
            for i in itos:
                parent = i.parent
                yield from self.to_ecs([] if parent is None else [parent], i)

        elif self.key == '.':
            yield from self.to_ecs(itos)  # Special case where each ito gets unique enumeration
            
        elif self.key == '><':
            rv = list(dict.fromkeys(itos))
            if reverse:
                rv.reverse()
            yield from self.to_ecs(rv)
            
        elif self.key == '*':
            for i in itos:
                yield from self.to_ecs(reversed(i.children) if reverse else i.children, i)

        elif self.key == '**':
            for i in itos:
                yield from self.to_ecs(i.walk_descendants(reverse), i)

        elif self.key == '***':
            for i in itos:
                leaves = filter(lambda ito: len(ito.children) == 0, i.walk_descendants(reverse))
                yield from self.to_ecs(leaves, i)
                
        elif self.key == '<<<':
            for i in itos:
                if i.parent is None:
                    yield from self.to_ecs([], i)
                    return
                
            root = i.find('....')
            if reverse:
                _iter = itertools.takewhile(lambda j: j is not i, root.walk_descendants(False))
            else:  # forward
                _iter = itertools.dropwhile(lambda j: j is not i, root.walk_descendants(True))
                next(_iter)  # advance to node after i

            ancestors = [*i.find_all('...')]
            _iter = filter(lambda j: j not in ancestors, _iter)

            yield from self.to_ecs(_iter, i)

        elif self.key == '<<':
            for i in itos:
                if (p := i.parent) is None:
                    sliced: typing.List[pawpaw.Ito] = []
                else:
                    idx = p.children.index(i)
                    sliced = p.children[:idx]
                    if not reverse:
                        sliced.reverse()
                    
                yield from self.to_ecs(sliced, i)

        elif self.key == '<':
            for i in itos:
                sibling = []
                if (p := i.parent) is not None:
                    idx = p.children.index(i)
                    if idx > 0:
                        sibling = [p.children[idx - 1]]
                
                yield from self.to_ecs(sibling, i)

        elif self.key == '>':
            for i in itos:
                sibling = []
                if (p := i.parent) is not None:
                    idx = p.children.index(i)
                    if idx < len(p.children) - 1:
                        sibling = [p.children[idx + 1]]

                yield from self.to_ecs(sibling, i)                        

        elif self.key == '>>':
            for i in itos:
                if (p := i.parent) is None:
                    sliced: typing.List[pawpaw.Ito] = []
                else:
                    idx = p.children.index(i)
                    sliced = p.children[idx + 1:]
                    if reverse:
                        sliced.reverse()
                
                yield from self.to_ecs(sliced, i)

        elif self.key == '>>>':
            for i in itos:
                if i.parent is None:
                    yield from self.to_ecs([], i)
                    return

            root = i.find('....')
            if reverse:
                _iter = itertools.takewhile(lambda j: j.start >= i.stop, root.walk_descendants(True))
            else:  # forward
                _iter = itertools.dropwhile(lambda j: j.start < i.stop, root.walk_descendants(False))

            yield from self.to_ecs(_iter, i)

        else:
            raise ValueError(f'invalid axis key \'{self.key}\'')


class Ecf(ABC):
    @classmethod
    def validate_values(cls, values: pawpaw.Types.C_VALUES) -> pawpaw.Types.C_VALUES:
        if values is None:
            raise ValueError('value expression found, however, no values dictionary supplied')
        return values
    
    @classmethod
    def validate_predicates(cls, predicates: pawpaw.Types.C_QPS) -> pawpaw.Types.C_QPS:
        if predicates is None:
            raise ValueError('predicate expression found, however, no predicates dictionary supplied')
        return predicates
    
    @abstractmethod
    def func(self, ec: pawpaw.Types.C_EITO, values: pawpaw.Types.C_VALUES, predicates: pawpaw.Types.C_QPS) -> bool:
        pass
    
    
class EcfTautology(Ecf):
    def func(self, ec: pawpaw.Types.C_EITO, values: pawpaw.Types.C_VALUES, predicates: pawpaw.Types.C_QPS) -> bool:
        return True
    

class EcfCombined(Ecf):
    _obs_pat_1 = r'(?<!\\)(?:(?:\\{2})*)'  # Odd number of backslashes ver 1
    _obs_pat_2 = r'\\(\\\\)*'  # Odd number of backslashes ver 2

    def __init__(
            self,
            ito: pawpaw.Ito,
            filters: list[pawpaw.Types.P_EITO_V_QPS],
            operands: list[pawpaw.Ito]
    ):
        self.ito = ito
        
        if len(filters) == 0:
            raise ValueError(f'empty filters list')

        if len(operands) != len(filters) + 1:
            raise ValueError(f'count of operands ({len(operands)}) must be one more than count of filters ({len(filters)})')

        for operand in operands:
            for c in str(operand):
                if c not in OPERATORS.keys() and c not in ' ()':
                    raise ValueError(f'invalid character \'{c}\' found in operand \'{operand}\' in {ito}')

        if sum(op.str_count('(') for op in operands) != sum(op.str_count(')') for op in operands):
            raise QueryErrors.unbalanced_parentheses(ito)

        while True:
            last_open_i, last_open_op = next(((i, operands[i]) for i in range(len(operands) - 1, -1, -1) if operands[i].str_find('(') > -1), (None, None))

            if last_open_i is None:
                break

            operands[last_open_i], discard, tmp = last_open_op.str_rpartition('(')
            if tmp.str_find(')') > -1:
                raise QueryErrors.empty_parentheses(ito, last_open_op)
            last_open_op = tmp

            next_closed_i, next_closed_op = next(((i, operands[i]) for i in range(last_open_i + 1, len(operands)) if operands[i].str_find(')') > -1), (None, None))
            if next_closed_i is None:
                raise QueryErrors.unbalanced_parentheses(ito)
            next_closed_op, discard, operands[next_closed_i] = next_closed_op.str_partition(')')

            if next_closed_i - last_open_i == 1:  # don't need to combine a single filter, so just add any post-parentheses ops back in
                operands[last_open_i] = last_open_op
            else:
                subf = EcfCombined(ito, filters[last_open_i:next_closed_i], [last_open_op, *operands[last_open_i + 1:next_closed_i], next_closed_op]).func
                filters[last_open_i:next_closed_i] = [subf]
                del operands[last_open_i + 1:next_closed_i]

        self.filters = filters
        self.operands = operands

    @classmethod
    def _eval(cls, operand: pawpaw.Ito, filter_: pawpaw.Types.P_EITO_V_QPS, ec, values, predicates):
        rv = filter_(ec, values, predicates)

        if operand.str_count('~') & 1 == 1:  # bitwise op to determine if n is odd
            rv = not rv
        
        return rv

    @classmethod
    def _highest_precedence_diadic(cls, ops: typing.List[pawpaw.Ito]) -> typing.Tuple[int, typing.Callable]:
        for k, f in OPERATORS.items():
            if k == '~':
                continue

            for i, op in enumerate(ops):
                if k in str(op):
                    return i, f

    def func(self, ec: pawpaw.Types.C_EITO, values: pawpaw.Types.C_VALUES, predicates: pawpaw.Types.C_QPS) -> bool:
        vals = [self._eval(self.operands[i], f, ec, values, predicates) for i, f in enumerate(self.filters)]
        ops = self.operands[1:-1]

        while len(vals) > 1:
            i, op = self._highest_precedence_diadic(ops)
            combined = op(vals[i], vals[i + 1])
            vals[i:i + 2] = [combined]
            del ops[i]

        return vals[0]


class EcfFilter(EcfCombined):
    _re_open_bracket = regex.compile(EcfCombined._obs_pat_1 + r'\[', regex.DOTALL)
    _re_close_bracket = regex.compile(EcfCombined._obs_pat_1 + r'\]', regex.DOTALL)

    _re = regex.compile(r'\[(?P<not>\~)?(?P<k>[a-z\-]+):\s*(?P<v>.+?)\]', regex.DOTALL)
    _re_balanced_splitter = regex.compile(
        r'(?P<bra>(?<!' + EcfCombined._obs_pat_2 + r')\[(?:(?:' + EcfCombined._obs_pat_2 + r'[\[\]]|[^\[\]])++|(?&bra))*(?<!' + EcfCombined._obs_pat_2 + r')\])',
        regex.DOTALL
    )

    @classmethod
    def _func(cls, not_: str, key: str, value: str) -> pawpaw.Types.P_EITO_V_QPS:
        if key in FILTER_KEYS['desc']:
            if not_ == '~':
                return lambda ec, values, predicates: ec.ito.desc not in [descape(s) for s in pawpaw.split_unescaped(value, ',')]
            else:
                return lambda ec, values, predicates: ec.ito.desc in [descape(s) for s in pawpaw.split_unescaped(value, ',')]

        if key in FILTER_KEYS['str']:
            if not_ == '~':
                return lambda ec, values, predicates: str(ec.ito) not in [descape(s) for s in pawpaw.split_unescaped(value, ',')]
            else:
                return lambda ec, values, predicates: str(ec.ito) in [descape(s) for s in pawpaw.split_unescaped(value, ',')]

        if key in FILTER_KEYS['str-casefold']:
            if not_ == '~':
                return lambda ec, values, predicates: str(ec.ito).casefold() not in [
                    descape(s).casefold() for s in pawpaw.split_unescaped(value.casefold(), ',')
                ]
            else:
                return lambda ec, values, predicates: str(ec.ito).casefold() in [
                    descape(s).casefold() for s in pawpaw.split_unescaped(value.casefold(), ',')
                ]

        if key in FILTER_KEYS['str-casefold-ew']:
            if not_ == '~':
                return lambda ec, values, predicates: all(not str(ec.ito).casefold().endswith(descape(s).casefold()) for s in pawpaw.split_unescaped(value.casefold(), ','))
            else:
                return lambda ec, values, predicates: any(str(ec.ito).casefold().endswith(descape(s).casefold()) for s in pawpaw.split_unescaped(value.casefold(), ','))

        if key in FILTER_KEYS['str-casefold-sw']:
            if not_ == '~':
                return lambda ec, values, predicates: all(not str(ec.ito).casefold().startswith(descape(s).casefold()) for s in pawpaw.split_unescaped(value.casefold(), ','))
            else:
                return lambda ec, values, predicates: any(str(ec.ito).casefold().startswith(descape(s).casefold()) for s in pawpaw.split_unescaped(value.casefold(), ','))

        if key in FILTER_KEYS['str-ew']:
            if not_ == '~':
                return lambda ec, values, predicates: all(not ec.ito.str_endswith(descape(s)) for s in pawpaw.split_unescaped(value, ','))
            else:
                return lambda ec, values, predicates: any(ec.ito.str_endswith(descape(s)) for s in pawpaw.split_unescaped(value, ','))

        if key in FILTER_KEYS['str-sw']:
            if not_ == '~':
                return lambda ec, values, predicates: all(not ec.ito.str_startswith(descape(s)) for s in pawpaw.split_unescaped(value, ','))
            else:
                return lambda ec, values, predicates: any(ec.ito.str_startswith(descape(s)) for s in pawpaw.split_unescaped(value, ','))

        if key in FILTER_KEYS['index']:
            ranges = list[tuple[int]]()

            for i_chunk in value.split(','):
                try:
                    vals = i_chunk.split('-')
                    if len(vals) > 2:
                        raise ValueError()

                    vals[0] = int(vals[0])
                    
                    if len(vals) == 2:
                        val2 = vals[1]
                        if val2.isdigit():
                            val2 = int(val2)
                        elif val2 == '' or val2.isspace():
                            val2 = float('inf')
                        else:
                            raise ValueError()
                        vals[1] = val2
                        vals = tuple(vals)

                    else:  # len == 1
                        vals = (vals[0], vals[0] + 1)

                except ValueError:
                    raise ValueError(f'invalid filter index value \'{i_chunk}\'')

                ranges.append(vals)

            if not_ == '~':
                return lambda ec, values, predicates: not any(r[0] <= ec.index < r[1] for r in ranges)
            else:
                return lambda ec, values, predicates: any(r[0] <= ec.index < r[1] for r in ranges)

        if key in FILTER_KEYS['predicate']:
            keys = [descape(s) for s in pawpaw.split_unescaped(value, ',')]
            if not_ == '~':
                return lambda ec, values, predicates: all(not p(ec) for p in [v for k, v in cls.validate_predicates(predicates).items() if k in keys])
            else:
                return lambda ec, values, predicates: all(p(ec) for p in [v for k, v in cls.validate_predicates(predicates).items() if k in keys])

        if key in FILTER_KEYS['value']:
            keys = [descape(s) for s in pawpaw.split_unescaped(value, ',')]
            if not_ == '~':
                return lambda ec, values, predicates: ec.ito.value() not in [v for k, v in cls.validate_values(values).items() if k in keys]
            else:
                return lambda ec, values, predicates: ec.ito.value() in [v for k, v in cls.validate_values(values).items() if k in keys]

        raise ValueError(f'unknown filter key \'{key}\'')

    def __init__(self, ito: pawpaw.Ito):
        filters: typing.List[pawpaw.Types.P_EITO_V_QPS] = []
        operands: typing.List[pawpaw.Types.P_EITO_V_QPS] = []

        if len([*ito.regex_finditer(self._re_open_bracket)]) != len([*ito.regex_finditer(self._re_close_bracket)]):
            raise ValueError(f'unbalanced brackets in filter(s) \'{ito}\'')

        last = None
        for i, f in enumerate(ito.regex_finditer(self._re_balanced_splitter)):
            start = ito.start if last is None else last.span(0)[1]
            stop = f.span(0)[0]

            op = pawpaw.Ito(ito.string, start, stop).str_strip()
            if i > 0 and len(op) == 0:
                raise ValueError(f'missing operator between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
            operands.append(op)

            m = self._re.fullmatch(f.group(0))
            if m is None:
                raise ValueError(f'invalid filter \'{f.group(0)}\'')
            filters.append(self._func(m.group('not'), m.group('k'), m.group('v')))
            last = f

        if last is not None:
            op = pawpaw.Ito(ito.string, last.span(0)[1], ito.stop)
            operands.append(op)

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
    def _func(cls, sq: pawpaw.Ito) -> pawpaw.Types.P_EITO_V_QPS:
        query = Query(sq)
        return lambda e, v, p: next(query.find_all(e.ito, v, p), None) is not None
    
    def __init__(self, ito: pawpaw.Ito):
        subqueries: typing.List[pawpaw.Types.P_EITO_V_QPS] = []
        operands: typing.List[pawpaw.Ito] = []

        m = ito.regex_search(self._re)
        if m is None:
            raise ValueError(f'Invalid parameter \'subquery\' value: {ito}')

        sqm = pawpaw.Ito.from_match(m, group_keys=['sq'])[0]
        if sum(1 for i in sqm.regex_finditer(self._re_open_cur)) != sum(1 for i in sqm.regex_finditer(self._re_close_cur)):
            raise ValueError(f'unbalanced curly braces in sub-query(ies) \'{sqm}\'')

        last: regex.Match | None = None
        for i, sq in enumerate(sqm.regex_finditer(self._re_balanced_splitter)):
            start = ito.start if last is None else last.span(0)[1]
            stop = sq.span(0)[0]

            op = pawpaw.Ito(ito.string, start, stop).str_strip()
            if i > 0 and len(op) == 0:
                raise ValueError(f'missing operator between subqueries \'{last}\' and \'{sq}\'')
            operands.append(op)

            subqueries.append(self._func(pawpaw.Ito.from_match(sq)[0][1:-1]))
            last = sq

        if last is not None:
            op = pawpaw.Ito(ito.string, last.span(0)[1], ito.stop)
            operands.append(op)

        super().__init__(ito, subqueries, operands)


class Phrase:
    def __init__(self, phrase: pawpaw.Ito):
        self.ito = phrase
        self.axis = Axis(phrase)
        
        unesc_curl = next(pawpaw.find_unescaped(phrase, '{', start=len(self.axis.ito)), phrase.stop)

        subq_ito = phrase[unesc_curl:].str_strip()
        if len(subq_ito) == 0:
            self.subquery = EcfTautology()
        else:
            while str(self.ito[i := unesc_curl - 1]) in ''.join(OPERATORS.keys()) + '() ~':
                unesc_curl = i
            subq_ito = phrase[unesc_curl:].str_strip()
            self.subquery = EcfSubquery(subq_ito)

        filt_ito = phrase[len(self.axis.ito):unesc_curl].str_strip()
        if len(filt_ito) == 0:
            self.filter = EcfTautology()
        else:
            self.filter = EcfFilter(filt_ito)

    def combined(self, ec: pawpaw.Types.C_EITO, values: pawpaw.Types.C_VALUES, predicates: pawpaw.Types.C_QPS) -> bool:
        return self.filter.func(ec, values, predicates) and self.subquery.func(ec, values, predicates)

    def find_all(
            self,
            itos: pawpaw.Types.C_IT_ITOS,
            values: pawpaw.Types.C_VALUES,
            predicates: pawpaw.Types.C_QPS
    ) -> pawpaw.Types.C_IT_ITOS:
        func = lambda ec: self.combined(ec, values, predicates)
        yield from (ec.ito for ec in filter(func, self.axis.find_all(itos)))


class Query:
    @classmethod
    def _split_phrases(cls, ito_path: pawpaw.Ito) -> typing.Iterable[pawpaw.Ito]:
        ls = 0
        esc = False
        subquery_cnt = 0
        for i, ito in enumerate(ito_path):
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
                yield ito_path[i-ls:i]
                ls = 0
            else:
                ls += 1

        if esc:
            raise ValueError('found escape with no succeeding character in \'{ito_path}\'')
        else:
            i += 1
            yield ito_path[i-ls:i]

    def __init__(self, path: pawpaw.Types.C_QPATH):
        """Creates a compiled query that can be used to search an Ito hierarchy

        Args:
            path: one or more phrases, separated by foreslashes:

                path := {phrase}[/phrase][/phrase]...

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
        if isinstance(path, str):
            path = pawpaw.Ito(path)
            
        if not isinstance(path, pawpaw.Ito):
            raise pawpaw.Errors.parameter_invalid_type('path', path, pawpaw.Types.C_QPATH)
            
        if len(path) == 0 or not path.str_isprintable():
            raise pawpaw.Errors.parameter_neither_none_nor_empty('path')

        self.phrases = [Phrase(p) for p in self._split_phrases(path)]

    def find_all(
        self,
        ito: pawpaw.Ito,
        values: pawpaw.Types.C_VALUES = None,
        predicates: pawpaw.Types.C_QPS = None
    ) -> pawpaw.Types.C_IT_ITOS:
        cur = [ito]
        for phrase in self.phrases:
            cur = phrase.find_all(cur, values, predicates)
        yield from cur

    def find(
        self,
        ito: pawpaw.Ito,
        values: pawpaw.Types.C_VALUES = None,
        predicates: pawpaw.Types.C_QPS = None
    ) -> pawpaw.Ito | None:
        return next(self.find_all(ito, values, predicates), None)


def compile(path: pawpaw.Types.C_QPATH) -> Query:
    return Query(path)


def find_all(
        path: pawpaw.Types.C_QPATH,
        ito: pawpaw.Ito,
        values: pawpaw.Types.C_VALUES = None,
        predicates: pawpaw.Types.C_QPS = None
) -> pawpaw.Types.C_IT_ITOS:
    yield from Query(path).find_all(ito, values, predicates)


def find(
        path: pawpaw.Types.C_QPATH,
        ito: pawpaw.Ito,
        values: pawpaw.Types.C_VALUES = None,
        predicates: pawpaw.Types.C_QPS = None
) -> pawpaw.Ito | None:
    return next(find_all(path, ito, values, predicates), None)
