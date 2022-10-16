from __future__ import annotations
import collections.abc
import operator
import typing

import regex
import segments


OPERATORS = collections.OrderedDict()
OPERATORS['&'] = operator.and_
OPERATORS['|'] = operator.or_
OPERATORS['^'] = operator.xor

FILTER_KEYS = collections.OrderedDict()
FILTER_KEYS['desc'] = 'desc', 'd'
FILTER_KEYS['string'] = 'string', 's'
FILTER_KEYS['string-casefold'] = 'string-casefold', 'scf', 'lcs'
FILTER_KEYS['index'] = 'index', 'i'
FILTER_KEYS['predicate'] = 'predicate', 'p'
FILTER_KEYS['value'] = 'value', 'v'

MUST_ESCAPE_CHARS = ('\\', '[', ']', '/', ',', '{', '}',)


class EC(typing.NamedTuple):
    index: int
    ito: segments.Types.C


C_IT_EC = typing.Iterable[EC]
C_VALUES = typing.Dict[str, typing.Any] | None
C_PREDICATES = typing.Dict[str, typing.Callable[[EC], bool]] | None
F_EC_2_EC = typing.Callable[[EC, C_VALUES, C_PREDICATES], EC]


def to_ecs(itos: segments.Types.C_IT_ITOS) -> C_IT_EC:
    yield from (EC(e, i) for e, i in enumerate(itos))


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


class _Axis:
    _RE = regex.compile(r'(?P<axis>(?P<key>\-|\.{1,4}|\*{1,3}|\<{1,2}|\>{1,2})\s*(?P<order>[nr]?))', regex.DOTALL)

    def __init__(self, phrase: segments.Types.C):
        m = phrase.regex_match(self._RE)
        if m is None:
            raise ValueError(f'invalid phrase \'{phrase}\'')
        self.ito = next(phrase.from_match_ex(m))

        try:
            self.key = next(i[:] for i in self.ito.children if i.desc == 'key')
        except StopIteration:
            raise ValueError(f'phrase \'{phrase[:]}\' missing axis key')

        self.order = next((i[:] for i in self.ito.children if i.desc == 'order'), None)

    def find_all(self, itos: typing.Iterable[segments.Types.C]) -> C_IT_EC:
        reverse = (self.order is not None and self.order[:] == 'r')

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
                yield from to_ecs(ancestors)

        elif self.key == '..':
            for i in itos:
                if (p := i.parent) is not None:
                    yield EC(0, p)

        elif self.key == '.':
            yield from to_ecs(itos)  # Special case where each ito gets unique enumeration

        elif self.key == '-':
            rv = list(collections.OrderedDict.fromkeys(itos))
            if reverse:
                rv.reverse()
            yield from to_ecs(rv)

        elif self.key == '*':
            for i in itos:
                if reverse:
                    yield from to_ecs(i.children[::-1])
                else:
                    yield from to_ecs(i.children)

        elif self.key == '**':
            for i in itos:
                if reverse:
                    yield from to_ecs([*i.walk_descendants()][::-1])
                else:
                    yield from to_ecs([*i.walk_descendants()])

        elif self.key == '***':
            for i in itos:
                if reverse:
                    yield from to_ecs([*(d for d in i.walk_descendants() if len(d.children) == 0)][::-1])
                else:
                    yield from to_ecs([*(d for d in i.walk_descendants() if len(d.children) == 0)])

        elif self.key == '<<':
            for i in itos:
                if (p := i.parent) is not None:
                    sliced = p.children[0:p.children.index(i)]
                    if reverse:
                        sliced.reverse()
                    yield from to_ecs(sliced)

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
                    yield from to_ecs(sliced)

        else:
            raise ValueError(f'invalid axis key \'{self.key}\'')


class _Subquery:
    _obs_pat_1 = r'(?<!\\)(?:(?:\\{2})*)'  # Odd number of backslashes ver 1
    _obs_pat_2 = r'\\(\\\\)*'  # Odd number of backslashes ver 2

    _open_bracket = regex.compile(_obs_pat_1 + r'\[', regex.DOTALL)
    _close_bracket = regex.compile(_obs_pat_1 + r'\]', regex.DOTALL)

    _open_cur = regex.compile(_obs_pat_1 + r'\{', regex.DOTALL)
    _close_cur = regex.compile(_obs_pat_1 + r'\}', regex.DOTALL)

    _subquery_re = regex.compile(_obs_pat_1 + r'(?P<sq>\{.*)\s*', regex.DOTALL)
    _subquery_balanced_splitter = regex.compile(
        r'(?P<cur>(?<!' + _obs_pat_2 + r')\{(?:(?:' + _obs_pat_2 + r'[{}]|[^{}])++|(?&cur))*(?<!' + _obs_pat_2 + r')\})',
        regex.DOTALL
    )

    def __init__(self, phrase: segments.Types.C, axis: _Axis):
        m = regex.search(self._subquery_re, phrase.string, pos=axis.ito.start, endpos=phrase.stop)
        if m is None:
            self.ito = None
            return

        self.ito = segments.Ito(phrase, stop=-len(m))
        self.subquery_operands = []
        self.subqueries = []

        m = regex.search(self._subquery_re, phrase.string, pos=axis.ito.start, endpos=phrase.stop)
        if m is not None:
            s_q_g = m.group('sq')
            if len([*self._open_cur.finditer(s_q_g)]) != len([*self._close_cur.finditer(s_q_g)]):
                raise ValueError(f'unbalanced curly braces in sub-query(ies) \'{s_q_g}\'')
            sqs = [*self._subquery_balanced_splitter.finditer(s_q_g)]
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
                self.subqueries.append(sq.group(0)[1:-1])
                last = sq


class _CombineAxisFilters:
    def __init__(self, filters: typing.Sequence[F_EC_2_EC], operands: typing.Sequence[str]):
        if len(filters) == 0:
            raise ValueError(f'empty filters list')
        self.filters = filters

        if len(operands) != len(filters) - 1:
            raise ValueError(f'count of operands ({len(operands):,}) must be one less than count of filters ({len(filters):,}')
        self.operands = operands

    def find_all(self, cur: C_IT_EC, values: C_VALUES, predicates: C_PREDICATES) -> C_IT_EC:
        for ec in cur:
            result = self.filters[0](ec, values, predicates)
            for f, o in zip(self.filters[1:], self.operands):
                op = OPERATORS.get(o)
                if op is None:
                    raise ValueError('invalid operator \'{o}\'')
                cur = f(ec, values, predicates)
                result = op(result, cur)
            if result:
                yield ec


class _Filter:
    _obs_pat_1 = r'(?<!\\)(?:(?:\\{2})*)'  # Odd number of backslashes ver 1
    _obs_pat_2 = r'\\(\\\\)*'  # Odd number of backslashes ver 2

    _open_bracket = regex.compile(_obs_pat_1 + r'\[', regex.DOTALL)
    _close_bracket = regex.compile(_obs_pat_1 + r'\]', regex.DOTALL)

    _open_cur = regex.compile(_obs_pat_1 + r'\{', regex.DOTALL)
    _close_cur = regex.compile(_obs_pat_1 + r'\}', regex.DOTALL)

    _filter_balanced_splitter = regex.compile(
        r'(?P<bra>(?<!' + _obs_pat_2 + r')\[(?:(?:' + _obs_pat_2 + r'[\[\]]|[^\[\]])++|(?&bra))*(?<!' + _obs_pat_2 + r')\])',
        regex.DOTALL
    )
    _filter_re = regex.compile(r'\[(?P<k>[a-z\-]+):\s*(?P<v>.+?)\]', regex.DOTALL)

    @classmethod
    def _split_on_comma(cls, value: str) -> typing.Iterable[str]:
        cur = ''
        escape = False
        for c in value:
            if escape:
                cur = f'{cur}\\{c}'
                escape = False
            elif c == '\\':
                escape = True
            elif c == ',':
                if len(cur) > 0:
                    yield cur
                cur = ''
            else:
                cur += c

        if len(cur) > 0:
            yield cur

    @classmethod
    def _filter_func_single(
        cls,
        key: str,
        value: str
    ) -> F_EC_2_EC:
        if key in FILTER_KEYS['desc']:
            return lambda ec, values, predicates: ec.ito.desc in [descape(s) for s in cls._split_on_comma(value)]

        if key in FILTER_KEYS['string']:
            return lambda ec, values, predicates: ec.ito[:] in [descape(s) for s in cls._split_on_comma(value)]

        if key in FILTER_KEYS['string-casefold']:
            return lambda ec, values, predicates: ec.ito[:].casefold() in [
                descape(s).casefold() for s in cls._split_on_comma(value.casefold())
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

            # TODO : predicates is None check needs to somehow be done
            # if predicates is None:
            #     raise ValueError('predicate expression found, however, no predicates dictionary supplied')

            keys = [descape(s) for s in cls._split_on_comma(value)]

            return lambda ec, values, predicates: any(p(ec) for p in [v for k, v in predicates.items() if k in keys])

        if key in FILTER_KEYS['value']:
            # TODO : values is None check needs to somehow be done
            # if values is None:
            #     raise ValueError('value expression found, however, no values dictionary supplied')

            keys = [descape(s) for s in cls._split_on_comma(value)]
            return lambda ec, values, predicates: ec.ito.value() in [v for k, v in values.items() if k in keys]

        raise ValueError(f'unknown filter key \'{key}\'')

    def __init__(
            self,
            phrase: segments.Types.C,
            axis: _Axis,
            subquery: _Subquery
    ):
        stop = None if subquery.ito is None else -len(subquery.ito)
        self.ito = segments.Ito(phrase, len(axis.ito), stop)
        self.ito = self.ito.str_strip()

        filters: typing.List[F_EC_2_EC] = []
        operands: typing.List[str] = []

        if len(self.ito) > 0:
            if len([*self.ito.regex_finditer(self._open_bracket)]) != len([*self.ito.regex_finditer(self._close_bracket)]):
                raise ValueError(f'unbalanced brackets in filter(s) \'{self.ito}\'')
            last = None
            for f in self.ito.regex_finditer(self._filter_balanced_splitter):
                if last is not None:
                    start = last.span(0)[1]
                    stop = f.span(0)[0]
                    op = self.ito.string[start:stop].strip()
                    if len(op) == 0:
                        raise ValueError(
                            f'missing operator between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
                    elif op not in OPERATORS.keys():
                        raise ValueError(
                            f'invalid filter operator \'{op}\' between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
                    operands.append(op)
                m = self._filter_re.fullmatch(f.group(0))
                if m is None:
                    raise ValueError(f'invalid filter \'{f.group(0)}\'')
                filters.append(self._filter_func_single(m.group('k'), m.group('v')))
                last = f

        if len(filters) == 0:
            self.combined_filter = lambda a, v, p: a
        else:
            self.combined_filter = _CombineAxisFilters(filters, operands).find_all

    def find_all(self, cur: C_IT_EC, values: C_VALUES, predicates: C_PREDICATES) -> C_IT_EC:
        yield from self.combined_filter(cur, values, predicates)


class _Phrase:
    def __init__(self, phrase: segments.Types.C):
        self.ito = phrase
        self.axis = _Axis(phrase)
        self.subquery = _Subquery(phrase, self.axis)
        self.filter = _Filter(phrase, self.axis, self.subquery)

    def find_all(
            self,
            itos: typing.Iterable[segments.Types.C],
            values: C_VALUES = None,
            predicates: C_PREDICATES = None
    ) -> segments.Types.C_IT_ITOS:
        yield from (ec.ito for ec in self.filter.find_all(self.axis.find_all(itos), values, predicates))  # TODO - chains these iterables?


class _Query:
    @classmethod
    def _split_phrases(cls, query: str) -> typing.Iterable[segments.Types.C]:
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

    def __init__(self, query: str):
        if query is None or len(query) == 0 or not query.isprintable():
            raise segments.Errors.parameter_neither_none_nor_empty('query')

        self.phrases = [_Phrase(p) for p in self._split_phrases(query)]

    def find_all(
            self,
            ito: segments.Types.C,
            values: typing.Dict[str, typing.Any] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, segments.Types.C], bool]] | None = None
    ) -> segments.Types.C_IT_ITOS:
        cur = [ito]
        for phrase in self.phrases:
            cur = phrase.find_all(cur, values, predicates)
        yield from cur


class _PhrasePart:
    OBS_PAT_1 = r'(?<!\\)(?:(?:\\{2})*)'  # Odd number of backslashes ver 1
    OBS_PAT_2 = r'\\(\\\\)*'              # Odd number of backslashes ver 2

    @classmethod
    def split_value_on_comma(cls, value: str) -> typing.Iterable[str]:
        cur = ''
        escape = False
        for c in value:
            if escape:
                cur = f'{cur}\\{c}'
                escape = False
            elif c == '\\':
                escape = True
            elif c == ',':
                if len(cur) > 0:
                    yield cur
                cur = ''
            else:
                cur += c

        if len(cur) > 0:
            yield cur


# class Filter(_PhrasePart):
#     KEYS = collections.OrderedDict()
#     KEYS['desc'] = 'desc', 'd'
#     KEYS['string'] = 'string', 's'
#     KEYS['string-casefold'] = 'string-casefold', 'scf', 'lcs'
#     KEYS['index'] = 'index', 'i'
#     KEYS['predicate'] = 'predicate', 'p'
#     KEYS['value'] = 'value', 'v'
#
#     MUST_ESCAPE_CHARS = ('\\', '[', ']', '/', ',', '{', '}',)
#
#     _OPEN_BRACKET_RE = regex.compile(_PhrasePart.OBS_PAT_1 + r'\[', regex.DOTALL)
#     _CLOSE_BRACKET_RE = regex.compile(_PhrasePart.OBS_PAT_1 + r'\]', regex.DOTALL)
#
#     _BALANCED_SPLITTER_RE = regex.compile(
#         r'(?P<bra>(?<!' + _PhrasePart.OBS_PAT_2 + r')\[(?:(?:' + _PhrasePart.OBS_PAT_2 + r'[\[\]]|[^\[\]])++|(?&bra))*(?<!' + _PhrasePart.OBS_PAT_2 + r')\])',
#         regex.DOTALL
#     )
#
#     _KEY_VALUE_RE = regex.compile(r'\[(?P<k>[a-z\-]+):\s*(?P<v>.+?)\]', regex.DOTALL)
#
#     @classmethod
#     def escape(cls, value: str) -> str:
#         rv = value.replace('\\', '\\\\')  # Must do backslash before other chars
#         for c in filter(lambda c: c != '\\', MUST_ESCAPE_CHARS):
#             rv = rv.replace(c, f'\\{c}')
#         return rv
#
#     @classmethod
#     def descape(cls, value: str) -> str:
#         rv = ''
#         escape = False
#         for c in value:
#             if escape or c != '\\':
#                 rv += c
#                 escape = False
#             else:
#                 escape = True
#
#         if escape:
#             raise ValueError(f'found escape with no succeeding character in \'value\'')
#
#         return rv
#
#     @classmethod
#     def _to_filter(
#             cls,
#             key: str,
#             value: str,
#             values: typing.Dict[str, typing.Any] | None = None,
#             predicates: typing.Dict[str, typing.Callable[[segments.Types.Axis], bool]] | None = None
#     ) -> segments.Types.F_AXIS_2_B:
#         if key in cls.Keys['desc']:
#             return lambda kvp: kvp[1].desc in [
#                 cls.deescape(s) for s in cls._query_value_split_on_comma(value)]
#
#         if key in cls.Keys['string']:
#             return lambda kvp: kvp[1][:] in [
#                 cls.deescape(s) for s in cls._query_value_split_on_comma(value)
#             ]
#
#         if key in cls.Keys['string-casefold']:
#             return lambda kvp: kvp[1][:].casefold() in [
#                 cls.deescape(s).casefold() for s in cls._query_value_split_on_comma(value.casefold())
#             ]
#
#         if key in cls.Keys['index']:
#             ints: typing.Set[int] = set()
#             for i_chunk in value.split(','):
#                 try:
#                     _is = [int(i.strip()) for i in i_chunk.split('-')]
#                 except:
#                     raise ValueError(f'invalid integer in \'value\'')
#
#                 len_is = len(_is)
#                 if len_is == 1:
#                     ints.add(_is[0])
#                 elif len_is == 2:
#                     for i in range(*_is):
#                         ints.add(i)
#                 else:
#                     raise ValueError('invalid index item \'value\'')
#
#             return lambda kvp: kvp[0] in ints
#
#         if key in cls.Keys['predicate']:
#             if predicates is None:
#                 raise ValueError('predicate expression found, however, no predicates dictionary supplied')
#
#             keys = [cls.deescape(s) for s in cls._query_value_split_on_comma(value)]
#             ps = [v for k, v in predicates.items() if k in keys]
#             return lambda kvp: any(p(*kvp) for p in ps)
#
#         if key in cls.Keys['value']:
#             if values is None:
#                 raise ValueError('value expression found, however, no values dictionary supplied')
#
#             keys = [cls.deescape(s) for s in cls._query_value_split_on_comma(value)]
#             vs = [v for k, v in values.items() if k in keys]
#             return lambda kvp: kvp[1].values() in vs
#
#         raise ValueError(f'unknown filter key \'{key}\'')
#
#     def parse(
#             self,
#             combined_filter: str,
#             values: typing.Dict[str, typing.Any] | None = None,
#             predicates: typing.Dict[str, typing.Callable[[segments.Types.Axis], bool]] | None = None
#     ) -> segments.Types.F_AXIS_2_B:
#         filter_operands = []
#         filters_funcs = []
#
#         if len(combined_filter) > 0:
#             if len([*self._OPEN_BRACKET_RE.finditer(combined_filter)]) != len([*self._CLOSE_BRACKET_RE.finditer(combined_filter)]):
#                 raise ValueError(f'unbalanced brackets in filter(s) \'{combined_filter}\'')
#             last = None
#             for f in self._BALANCED_SPLITTER_RE.finditer(combined_filter):
#                 if last is not None:
#                     slice_ = slice(*last.span(0))
#                     op = combined_filter[slice_].strip()
#                     if len(op) == 0:
#                         raise ValueError(
#                             f'missing operator between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
#                     elif op not in _Query.QUERY_OPERATORS.keys():
#                         raise ValueError(
#                             f'invalid filter operator \'{op}\' between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
#                     self.operands.append(op)
#                 m = self._KEY_VALUE_RE.fullmatch(f.group(0))
#                 if m is None:
#                     raise ValueError(f'invalid filter \'{f.group(0)}\'')
#                 self.filters.append({'key': m.group('k'), 'val': m.group('v')})
#                 last = f
#
#     def __init__(self, combined_filter: str):
#         self.filters: typing.Sequence[segments.Types.F_AXIS_2_B]
#         self.operands: typing.Sequence[str]
#         self.parse(combined_filter)
#         if len(self.filters) == 0:
#             raise ValueError(f'empty filters list')
#
#         if len(self.operands) != len(self.filters) - 1:
#             raise ValueError(f'count of operands ({len(self.operands):,}) must be one less than count of filters ({len(self.filters):,}')
#
#
#     @classmethod
#     def _from_phrase(
#             cls,
#             itos: typing.Iterable[segments.Types.C],
#             query_step: str,
#             values: typing.Dict[str, object] | None = None,
#             predicates: typing.Dict[str, typing.Callable[[int, segments.Types.C], bool]] | None = None
#     ) -> typing.Iterable[segments.Types.C]:
#         qsp = cls._PhraseParse(query_step)
#
#         axis = cls._axis_order_iter(itos, qsp.axis, qsp.order)
#
#         if len(qsp.filters) == 0:
#             filt = lambda a: True
#         else:
#             filt = cls._CombinedFilters(
#                 [cls._query_step_filter(f['key'], f['val'], values, predicates) for f in qsp.filters],
#                 qsp.filter_operands
#             ).filter
#
#     def filter(self, axis: segments.Types.Axis) -> bool:
#         acum = self.filters[0](axis)
#         for f, o in zip(self.filters[1:], self.operands):
#             op = _Query.QUERY_OPERATORS.get(o)
#             if op is None:
#                 raise ValueError('invalid operator \'{o}\'')
#             cur = f(axis)
#             acum = op(acum, cur)
#         return acum
#
#     def filter(self, axis: segments.Types.Axis) -> bool:
#         acum = self.filters[0](axis)
#         for f, o in zip(self.filters[1:], self.operands):
#             op = _Query.QUERY_OPERATORS.get(o)
#             if op is None:
#                 raise ValueError('invalid operator \'{o}\'')
#             cur = f(axis)
#             acum = op(acum, cur)
#         return acum
