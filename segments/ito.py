from __future__ import annotations
import bisect
import collections.abc
import inspect
import itertools
import json
import operator
import pickle
import types
import typing

import regex
from segments.span import Span
from segments.errors import Errors


class Types:
    C = typing.TypeVar('C', bound='Ito')

    F_ITO_2_ITOR = typing.Callable[[C], 'Itorator']

    C_SQ_ITOS = typing.Sequence[C]
    F_ITO_2_SQ_ITOS = typing.Callable[[C], C_SQ_ITOS]

    C_IT_ITOS = typing.Iterable[C]
    F_ITO_2_IT_ITOS = typing.Callable[[C], C_IT_ITOS]

    @classmethod
    def is_callable(cls, val: typing.Any, *params: typing.Type) -> bool:
        if not isinstance(val, typing.Callable):
            return False

        ips = inspect.signature(val).parameters
        if len(params) != len(ips):
            return False

        for ipv, p in zip(ips.values(), params):
            if ipv.annotation != inspect._empty and p != ipv.annotation:  # TODO : when p is singular type and annotation is Union
                return False

        return True


class Ito:
    @classmethod
    def _to_span(cls, src | Ito, start: int | None = None, stop: int | None = None, desc: str | None = None) -> Span:
        if isinstance(src, str):
            offset = 0
        elif isinstance(src, Ito):
            offset = src.start
        else:
            raise Errors.parameter_invalid_type('src', src, str, Ito)
            
        return Span.from_indices(src, start, stop, offset)
    
    # region ctors & clone

    def __init__(
            self,
            src: str | Ito,  # Rename to 'val'?
            start: int | None = None,
            stop: int | None = None,
            desc: str | None = None
    ):
        self._span = self._to_span(src, start, stop)  # Checks first 3 params
        
        self._string = src.string if isinstance(src, Ito) else src

        if desc is not None and not isinstance(desc, str):
            raise Errors.parameter_invalid_type('desc', desc, str)
        self.desc = desc

        self._value_func: typing.Callable[[Ito], typing.Any] | None = None

        self._parent = None
        self._children = ChildItos(self)

    @classmethod
    def from_match(cls,
                   match: regex.Match,
                   group: str | int = 0,
                   desc: str = None
                   ) -> C:
        if match is None:
            raise Errors.parameter_not_none('match')
        elif not isinstance(match, regex.Match):
            raise Errors.parameter_invalid_type('match', match, regex.Match)

        if group is None:
            raise Errors.parameter_not_none('group')

        return cls(match.string, *match.span(group), desc=desc)

    @classmethod
    def _group_filter(
            cls,
            group_filter: typing.Iterable[str] | typing.Callable[[regex.Match, str], bool] | None
    ) -> typing.Callable[[regex.Match, str], bool]:
        if group_filter is None:
            return lambda m_, g: True

        if isinstance(group_filter, typing.Callable):  # TODO : Better type check
            return group_filter

        if hasattr(group_filter, '__contains__'):
            return lambda m_, g: g in group_filter

        raise Errors.parameter_invalid_type(
            'group_filter',
            group_filter,
            typing.Iterable[str],
            typing.Callable[[Ito, regex.Match, str], bool],
            types.NoneType)

    @classmethod
    def from_re(
            cls,
            re: regex.Pattern,
            src: str | Ito,
            desc_func: typing.Callable[[regex.Match, str], str] = lambda match, group: group,
            group_filter: typing.Iterable[str] | typing.Callable[[regex.Match, str], bool] | None = None,
            limit: int | None = None,
    ) -> typing.Iterable[C]:
        if isinstance(src, str):
            s = src
            span = Span.from_indices(s)
        elif isinstance(src, Ito):
            s = src.string
            span = src.span
        else:
            raise Errors.parameter_invalid_type('src', src, str, Ito)
        for count, m in enumerate(re.finditer(s, *span), 1):
            path_stack: typing.List[Ito] = []
            match_itos: typing.List[Ito] = []
            filtered_gns = (gn for gn in m.re.groupindex.keys() if cls._group_filter(group_filter)(m, gn))
            span_gns = ((span, gn) for gn in filtered_gns for span in m.spans(gn))
            for span, gn in sorted(span_gns, key=lambda val: (val[0][0], -val[0][1])):
                ito = Ito(s, *span, desc_func(m, gn))
                while len(path_stack) > 0 and (ito.start < path_stack[-1].start or ito.stop > path_stack[-1].stop):
                    path_stack.pop()
                if len(path_stack) == 0:
                    match_itos.append(ito)
                else:
                    path_stack[-1].children.add(ito)

                path_stack.append(ito)

            yield from match_itos

            if limit is not None and count >= limit:
                break

    @classmethod
    def from_spans(cls, string: str, *spans: Span, desc: str | None = None) -> typing.Iterable[C]:
        return [cls(string, *s, desc=desc) for s in spans]

    @classmethod
    def from_substrings(
            cls,
            src: str | Ito,
            *substrings: str,
            desc: str | None = None
    ) -> typing.Iterable[C]:
        """
        :param src:
        :param substrings: must be:
            1. present in string
            2. ordered left to right
            3. non-overlapping

            * substrings do not have to be consecutive

            * to capture a repeated substring, it must be repeated in the substrings parameter, e.g.:

            given:

                string = 'ababce'

            when substrings =

                ('ab', 'ce') -> returns 2 Ito objects with spans (0,2) and (4,6)

                ('ab', 'ab', 'ce') -> returns 3 Ito objects with spans (0,2), (2,4) and (4,6)
        :param desc:
        :return:
        """
        if isinstance(src, str):
            s = src
            i, j = Span.from_indices(src)
        elif isinstance(src, Ito):
            s = src.string
            i, j = src.span
        else:
            raise Errors.parameter_invalid_type('src', src, str, Ito)
        for sub in substrings:
            i = s.index(sub, i, j)
            k = i + len(sub)
            yield cls(s, i, k, desc)
            i = k

    def clone(self,
              start: int | None = None,
              stop: int | None = None,
              desc: str | None = None,
              clone_children: bool = True
              ) -> C:
        rv = self.__class__(
            self._string,
            self.start if start is None else start,
            self.stop if stop is None else stop,
            self.desc if desc is None else desc
        )

        if self._value_func is not None:
            rv.value_func = self._value_func

        if clone_children:
            rv.children.add(*(c.clone() for c in self._children))

        return rv

    # endregion

    # region properties

    @property
    def string(self) -> str:
        return self._string

    @property
    def span(self) -> Span:
        return self._span

    @property
    def start(self) -> int:
        return self._span.start

    @property
    def stop(self) -> int:
        return self._span.stop

    @property
    def parent(self) -> Ito:
        return self._parent

    def _set_parent(self, parent: Ito) -> None:
        if self._string != parent._string:
            raise ValueError(f'parameter \'parent\' has a different value for .string')
        if self.start < parent.start or self.stop > parent.stop:
            raise ValueError(f'parameter \'parent\' has incompatible .span {parent.span}')
        if self is parent:
            raise ValueError(f'parameter \'parent\' can\'t be self')
        self._parent = parent

    @property
    def children(self) -> ChildItos:
        return self._children

    def value(self) -> typing.Any:
        return self.__str__()

    @property
    def value_func(self) -> typing.Callable[[Ito], typing.Any]:
        return self._value_func

    @value_func.setter
    def value_func(self, f: typing.Callable[[Ito], typing.Any]) -> None:
        if f is None:
            delattr(self, 'value')
        else:
            setattr(self, 'value', f.__get__(self))
        self._value_func = f

    # endregion

    # region serialization

    # region pickling

    @classmethod
    def pickle_loads(cls, pickle_str: str, ito_str: str) -> Ito:
        rv = pickle.load(pickle_str)
        rv._string = ito_str
        return rv

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['parent']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._parent = None
        for child in self.children:
            child._parent = self

    # endregion

    # region JSON

    class JsonEncoderStringless(json.JSONEncoder):
        def default(self, o: typing.Any) -> typing.Dict:
            return {
                '__type__': 'Ito',
                '_span': o.span,
                'desc': o.desc,
                'children': [self.default(c) for c in o.children]
            }

    class JsonEncoder(json.JSONEncoder):
        def default(self, o: typing.Any) -> typing.Dict:
            return {
                '__type__': 'Ito',
                'string': o.string,
                'ito': Ito.JsonEncoderStringless.default(o)
            }

    @classmethod
    def json_decoder_stringless(cls, obj: typing.Dict) -> Ito | typing.Dict:
        if (t := obj.get('__type__')) is not None and t == 'Ito':
            rv = Ito('', desc=obj['desc'])
            rv._span = Span(obj['desc'])
            rv.children.add(obj['children'])
            return rv
        else:
            return obj

    @classmethod
    def json_decoder(cls, obj: typing.Dict) -> Ito | typing.Dict:
        if (t := obj.get('__type__')) is not None:
            if t == 'Tuple[str, Ito]':
                rv = obj['ito']
                rv._string = obj['string']
                return rv
        elif t == 'Ito':
            return cls.json_decoder_stringless(obj)
        else:
            return obj

    # endregion

    # endregion

    # region __x__ methods

    def __repr__(self) -> str:
        # TODO : Add children to repr str?
        return f'segments.Ito({self._string.__repr__()}, {self.start}, {self.stop}, {self.desc.__repr__()})'

    def __str__(self) -> str:
        return self._string[slice(*self.span)]


    def __len__(self) -> int:
        return self.stop - self.start

    def __getitem__(self, key: int | slice) -> str:
        if isinstance(key, int):
            span = Span.from_indices(self, key, None, self.start)
            return self._string[span.start]

        if isinstance(key, slice):
            span = Span.from_indices(self, key.start, key.stop, self.start)
            return self._string[slice(*span)]

        raise Errors.parameter_invalid_type('key', key, int, slice)

    # endregion

    # region combinatorics

    @classmethod
    def join(cls, *itos: C, desc: str | None = None) -> C:
        it_str, it_start, it_stop, it_children = itertools.tee(itos, 4)

        strs = set(ito.string for ito in it_str)
        if len(strs) > 1:
            raise ValueError(f'parameter \'{itos}\' have differing values for .string')

        start = min(ito.start for ito in it_start)
        stop = max(ito.stop for ito in it_stop)
        rv = Ito(strs.pop(), start, stop, desc)

        children: typing.Iterable[Ito] = itertools.chain.from_iterable(ito.children for ito in itos)
        rv.children.add(*(c.clone() for c in children))

        return rv

    # endregion

    # region regex equivalence methods

    def regex_finditer(self, re: regex.Pattern) -> typing.Iterable[regex.Match]:
        return re.finditer(self.string, *self.span)

    def regex_match(self, re: regex.Pattern) -> regex.Match:
        return re.match(self.string, *self.span)

    def regex_search(self, re: regex.Pattern) -> regex.Match:
        return re.search(self.string, *self.span)
    
    def _regex_split(self, re: regex.Pattern) -> typing.Tuple(typing.List[Ito], typing.List[Ito])
        parts: typing.List[Ito] = []
        seps: typing.List[Ito] = []
        
        i = self.start
        for m in self.regex_inditer(re):
            if maxsplit != 0 and len(parts) > maxsplit:
                break
            span = Span(*m.span(0))
            seps.append(self.clone(*span))
            if span.start == i:
                parts.append(self.clone(i, i))
            else:
                parts.append(self.clone(i, span.start))
            i = span.stop
            
        if i < self.stop:
            parts.append(self.clone(i))
        elif i == self.stop:
            parts.append(self.clone(i, i))
            
        return parts, seps
    
    def _regex_split(self, re: regex.Pattern) -> typing.List[Ito]:
        return self._regex_split(re, maxsplit)[0]

    # endregion

    # region str equivalence methods

    def str_count(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.count(sub, *Span.from_indices(self, start, end, self.start))

    # region endswtih, startswtih
        
    def str_endswith(self, suffix: str | typing.Tuple[str, ...], start: int | None = None, end: int | None = None) -> bool:
        if suffix is None:
            raise Errors.parameter_invalid_type('suffix', suffix, str, typing.Tuple[str, ...])

        # The subsequent block captures the strange behavior of Python's str.endswith
        if start is not None and start != 0:
            ls = len(self)
            if start > ls:
                return False

            start_c = 0 if start is None else start if start >= 0 else ls + start
            end_c = ls if end is None else end if end >= 0 else ls + end
            if start_c > end_c:  # inconsistent start/end
                return False

        # Ok, just do what you would expect
        norms = Span.from_indices(self, start, end, self.start)
        return self._string.endswith(suffix, *norms)

    def str_startswith(
            self,
            prefix: str | typing.Tuple[str, ...],
            start: int | None = None,
            end: int | None = None
    ) -> bool:
        if prefix is None:
            raise Errors.parameter_invalid_type('prefix', prefix, str, typing.Tuple[str, ...])

        # The subsequent block captures the strange behavior of Python's str.startswith
        if start is not None and start != 0:
            ls = len(self)
            if start > ls:
                return False

            start_c = 0 if start is None else start if start >= 0 else ls + start
            end_c = ls if end is None else end if end >= 0 else ls + end
            if start_c > end_c:  # inconsistent start/end
                return False

        # Ok, just do what you would expect
        norms = Span.from_indices(self, start, end, self.start)
        return self._string.startswith(prefix, *norms)

    # endregion

    # region find, index, rfind, rindex
   
    def str_find(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.find(sub, *Span.from_indices(self, start, end, self.start))

    def str_index(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.index(sub, *Span.from_indices(self, start, end, self.start))
    
    def str_rfind(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.rfind(sub, *Span.from_indices(self, start, end, self.start))

    def str_rindex(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.rindex(sub, *Span.from_indices(self, start, end, self.start))

    # endregion

    # region 'is' predicates

    def __str_is_helper_all(self, predicate: typing.Callable[[str], bool]) -> bool:
        if self.start == self.stop:
            return predicate('')

        return all(predicate(self._string[i]) for i in range(self.start, self.stop))

    def __str_is_helper_any(self, predicate: typing.Callable[[str], bool]) -> bool:
        if self.start == self.stop:
            return predicate('')

        return any(predicate(self._string[i]) for i in range(self.start, self.stop))

    def str_isalnum(self):
        return self.__str_is_helper_all(str.isalnum)

    def str_isalpha(self):
        return self.__str_is_helper_all(str.isalpha)

    def str_isascii(self):
        return self.__str_is_helper_all(str.isascii)

    def str_isdecimal(self):
        return self.__str_is_helper_all(str.isdecimal)

    def str_isdigit(self):
        return self.__str_is_helper_all(str.isdigit)

    def str_isidentifier(self):
        return self.__str__().isidentifier()

    def str_islower(self):
        alphas = False
        for i in range(self.start, self.stop):
            c = self.string[i]
            if c.isalpha():
                alphas = True
                if not c.islower():
                    return False
        return alphas

    def str_isnumeric(self):
        return self.__str_is_helper_all(str.isnumeric)

    def str_isprintable(self):
        return self.__str_is_helper_any(str.isprintable)

    def str_isspace(self):
        return self.__str_is_helper_all(str.isspace)

    def str_istitle(self):
        return self.__str__().istitle()

    def str_isupper(self):
        alphas = False
        for i in range(self.start, self.stop):
            c = self.string[i]
            if c.isalpha():
                alphas = True
                if not c.isupper():
                    return False
        return alphas

    # endregion

    # region strip methods

    def __f_c_in(self, chars: str | None) -> typing.Callable[[int], bool]:
        if chars is None or chars == '':
            return lambda i: self._string[i].isspace()
        else:
            return lambda i: self._string[i] in chars

    def str_lstrip(self, chars: str | None = None) -> Ito:
        f_c_in = self.__f_c_in(chars)
        i = self.start
        while i < self.stop and f_c_in(i):
            i += 1
        return self.clone(i)

    def str_rstrip(self, chars: str | None = None) -> Ito:
        f_c_in = self.__f_c_in(chars)
        i = self.stop - 1
        while i >= 0 and f_c_in(i):
            i -= 1

        return self.clone(stop=i+1)

    def str_strip(self, chars: str | None = None) -> Ito:
        return self.str_lstrip(chars).str_rstrip(chars)

    # endregion

    # region partition and split methods

    def str_partition(self, sep) -> typing.Tuple[C, C, C]:
        if sep is None:
            raise ValueError('must be str, not NoneType')
        elif sep == '':
            raise ValueError('empty separator')
        else:
            i = self.str_find(sep)
            if i == -1:
                return self.clone(), self.clone(self.stop), self.clone(self.stop)
            else:
                return self.clone(stop=i), self.clone(i, i+len(sep)), self.clone(i+len(sep))

    def str_rpartition(self, sep) -> typing.Tuple[C, C, C]:
        if sep is None:
            raise ValueError('must be str, not NoneType')
        elif sep == '':
            raise ValueError('empty separator')
        else:
            i = self.str_rfind(sep)
            if i == -1:
                return self.clone(self.stop), self.clone(self.stop), self.clone()
            else:
                return self.clone(stop=i), self.clone(i, i + len(sep)), self.clone(i + len(sep))

    def __nearest_non_ws_sub(self, start: int, reverse: bool = False) -> Ito | None:
        if reverse:
            stop = -1
            step = -1
        else:
            stop = self.stop
            step = 1

        def from_idxs():
            if step == 1:
                return self.clone(non_ws_i, i)
            else:
                return self.clone(i + 1, non_ws_i + 1)

        non_ws_i: 0
        in_ws = True
        for i in range(start, stop, step):
            c = self[i]
            if in_ws:
                if not c.isspace():
                    non_ws_i = i
                    in_ws = False
            else:
                if c.isspace():
                    return from_idxs()

        if not in_ws:
            i += step
            return from_idxs()

    def str_rsplit(self, sep: str = None, maxsplit: int = -1) -> typing.List[Ito]:
        if sep is None:
            rv: typing.List[Ito] = []
            if self._string == '':
                return rv

            i = self.stop - 1
            rv: typing.List[Ito] = []
            while (sub := self.__nearest_non_ws_sub(i, True)) is not None and maxsplit != 0:
                rv.append(sub)
                i = sub.start - 1
                maxsplit -= 1
            rv.reverse()

            if maxsplit == 0:
                head_stop = self.stop if len(rv) == 0 else rv[0].start
                head = self.clone(stop=head_stop).str_rstrip()
                if len(head) > 0:
                    rv.insert(0, head)
            return rv

        elif not isinstance(sep, str):
            raise Errors.parameter_invalid_type('sep', sep, str, types.NoneType)

        elif sep == '':
            raise ValueError('empty separator')

        else:
            if maxsplit == 0:
                return [self.clone()]

            rv: typing.List[Ito] = []
            i = self.stop
            while (j := self._string.rfind(sep, self.start, i)) >= 0 and maxsplit != 0:
                rv.insert(0, self.clone(j + len(sep), i))
                i = j
                maxsplit -= 1
            # if i >= self.start + len(sep) and maxsplit != 0:
            #     rv.insert(0, self.clone(i - len(sep), i))
            if i >= self.start and maxsplit != 0:
                rv.insert(0, self.clone(stop=i))

            if maxsplit == 0:
                head_stop = self.stop if len(rv) == 0 else rv[0].start
                head = self.clone(stop=head_stop).str_removesuffix(sep)
                if len(head) > 0:
                    rv.insert(0, head)
            return rv

    def str_split(self, sep: str = None, maxsplit: int = -1) -> typing.List[Ito]:
        if sep is None:
            rv: typing.List[Ito] = []
            if self._string == '':
                return rv

            i = self.start
            while (sub := self.__nearest_non_ws_sub(i)) is not None and maxsplit != 0:
                rv.append(sub)
                i = sub.stop
                maxsplit -= 1

            if maxsplit == 0:
                tail_start = self.start if len(rv) == 0 else rv[-1].stop
                tail = self.clone(tail_start).str_lstrip()
                if len(tail) > 0:
                    rv.append(tail)
            return rv

        elif not isinstance(sep, str):
            raise Errors.parameter_invalid_type('sep', sep, str, types.NoneType)

        elif sep == '':
            raise ValueError('empty separator')

        else:
            if maxsplit == 0:
                return [self.clone()]

            rv: typing.List[Ito] = []
            i = self.start
            while (j := self._string.find(sep, i, self.stop)) >= 0 and maxsplit != 0:
                rv.append(self.clone(i, j))
                i = j + len(sep)
                maxsplit -= 1
            if i <= self.stop and maxsplit != 0:
                rv.append(self.clone(i))

            if maxsplit == 0:
                tail_start = self.start if len(rv) == 0 else rv[-1].stop
                tail = self.clone(tail_start).str_removeprefix(sep)
                if len(tail) > 0:
                    rv.append(tail)
            return rv

    # Line separators taken from https://docs.python.org/3/library/stdtypes.html
    _splitlines_re = regex.compile(r'\r\n|\r|\n|\v|\x0b|\f|\x0c|\x1c|\x1d|\x1e|\x85|\u2028|\u2029', regex.DOTALL)

    def str_splitlines(self, keepends: bool = False) -> typing.List[Ito]:
        parts, seps = self._regex_split(self._splitlines_re)
        if len(parts[-1]) == 0:
            del parts[-1]
            del seps[-1]
        if len(parts) == 0 or not keepends:
            return parts
        rv = [parts.pop(0)]
        for part, sep in zip(parts, seps):
            rv.append(part)
            rv.append(sep)
        return rv

    # endregion

    # region removeprefix, removesuffix

    def str_removeprefix(self, prefix: str) -> Ito:
        if self.str_startswith(prefix):
            return Ito(self, len(prefix), desc=self.desc)
        else:
            return self.clone()

    def str_removesuffix(self, suffix: str) -> Ito:
        if self.str_endswith(suffix):
            return Ito(self, stop=-len(suffix), desc=self.desc)
        else:
            return self.clone()
        
    # endregion

    # endregion

    # region traversal

    def get_root(self) -> Ito | None:
        rv = self
        while (parent := rv.parent) is not None:
            rv = parent
        return rv

    def walk_descendants_levels(self, start: int = 0) -> typing.Iterable[typing.Tuple[int, C]]:
        for child in self.children:
            yield start, child
            yield from child.walk_descendants_levels(start+1)

    def walk_descendants(self) -> typing.Iterable[C]:
        yield from (ito for lvl, ito in self.walk_descendants_levels())

    # endregion

    # region query

    _MUST_ESCAPE_FILTER_VALUE_CHARS = ('\\', '[', ']', '/', ',', '{', '}',)

    @classmethod
    def filter_value_escape(cls, value: str) -> str:
        rv = value.replace('\\', '\\\\')  # Must do backslash before other chars
        for c in filter(lambda c: c != '\\', cls._MUST_ESCAPE_FILTER_VALUE_CHARS):
            rv = rv.replace(c, f'\\{c}')
        return rv

    @classmethod
    def filter_value_descape(cls, value: str) -> str:
        rv = ''
        escape = False
        for c in value:
            if escape or c != '\\':
                rv += c
                escape = False
            else:
                escape = True

        if escape:
            raise ValueError(f'found escape with no succeeding character in \'value\'')

        return rv

    @classmethod
    def _query_value_split_on_comma(cls, value: str) -> typing.Iterable[str]:
        cur = ''
        escape = False
        for c in value:
            if escape:
                cur = f'{cur}\\{c}'
                escape = False
            elif c == '\\':
                escape = True
            elif c == ', ':
                if len(cur) > 0:
                    yield cur
                cur = ''
            else:
                cur += c

        if len(cur) > 0:
            yield cur

    @classmethod
    def _query_step_filter(
            cls,
            key: str,
            value: str,
            values: typing.Dict[str, typing.Any] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, Ito], bool]] | None = None
    ) -> typing.Callable[[typing.Tuple[int, Ito]], bool]:
        if key == 'd':
            return lambda kvp: kvp[1].desc in [
                cls.filter_value_descape(s) for s in cls._query_value_split_on_comma(value)]

        if key == 'i':
            ints: typing.Set[int] = set()
            for i_chunk in value.split(','):
                try:
                    _is = [int(i.strip()) for i in i_chunk.split('-')]
                except:
                    raise ValueError(f'invalid integer in \'value\'')

                len_is = len(_is)
                if len_is == 1:
                    ints.add(_is[0])
                elif len_is == 2:
                    for i in range(*_is):
                        ints.add(i)
                else:
                    raise ValueError('invalid index item \'value\'')

            return lambda kvp: kvp[0] in ints

        if key == 'p':
            if predicates is None:
                raise ValueError('predicate expression found, however, no predicates dictionary supplied')

            keys = [cls.filter_value_descape(s) for s in cls._query_value_split_on_comma(value)]
            ps = [v for k, v in predicates.items() if k in keys]
            return lambda kvp: any(p(*kvp) for p in ps)

        if key == 's':
            return lambda kvp: kvp[1].__str__() in [
                cls.filter_value_descape(s) for s in cls._query_value_split_on_comma(value)
            ]

        if key == 'sc':
            return lambda kvp: kvp[1].__str__().casefold() in [
                cls.filter_value_descape(s).casefold() for s in cls._query_value_split_on_comma(value)
            ]

        if key == 'v':
            if values is None:
                raise ValueError('value expression found, however, no values dictionary supplied')

            keys = [cls.filter_value_descape(s) for s in cls._query_value_split_on_comma(value)]
            vs = [v for k, v in values.items() if k in keys]
            return lambda kvp: kvp[1].values() in vs

        raise ValueError(f'invalid filter key \'key\'')

    QUERY_OPERATORS = collections.OrderedDict()
    QUERY_OPERATORS['&'] = operator.and_
    QUERY_OPERATORS['|'] = operator.or_
    QUERY_OPERATORS['^'] = operator.xor

    class _CombinedFilters:
        def __init__(self, filters: typing.Sequence[regex.Match], operands: typing.Sequence[str]):
            if len(filters) == 0:
                raise ValueError(f'empty filters list')
            self.filters = filters

            if len(operands) != len(filters) - 1:
                raise ValueError(f'count of operands ({len(operands):,}) must be one less than count of filters ({len(filters):,}')
            self.operands = operands

        def filter(self, kvp: typing.Tuple[int, Ito]) -> bool:
            acum = self.filters[0](kvp)
            for f, o in zip(self.filters[1:], self.operands):
                op = Ito.QUERY_OPERATORS.get(o)
                if op is None:
                    raise ValueError('invalid operator \'{o}\'')
                cur = f(kvp)
                acum = op(acum, cur)
            return acum

    class _CombinedSubqueries:
        def __init__(self, subqueries: typing.Sequence[str], operands: typing.Sequence[str]):
            if len(subqueries) == 0:
                raise ValueError('empty subqueries list')
            self.subqueries = subqueries

            if len(operands) != len(subqueries) - 1:
                raise ValueError(f'count of operands ({len(operands):,}) must be one less than count of subqueries ({len(subqueries):,}')
            self.operands = operands

        def filter(self, kvp: typing.Tuple[int, Ito]) -> bool:
            acum = kvp[1].find(self.subqueries[0]) is not None
            for s, o in zip(self.subqueries[1:], self.operands):
                op = Ito.QUERY_OPERATORS.get(o)
                if op is None:
                    raise ValueError('invalid operator \'{o}\'')
                cur = kvp[1].find(s) is not None
                acum = op(acum, cur)
            return acum

    class _PhraseParse:
        _axis_re = regex.compile(r'(?P<a>\-|\.{1,4}|\*{1,3}|\<{1,2}|\>{1,2})\s*(?P<o>[nr])?\s*(?P<r>.*)', regex.DOTALL)

        _obs_pat_1 = r'(?<!\\)(?:(?:\\{2})*)'  # Odd number of backslashes ver 1
        _obs_pat_2 = r'\\(\\\\)*'              # Odd number of backslashes ver 2

        _open_bracket = regex.compile(_obs_pat_1 + r'\[', regex.DOTALL)
        _close_bracket = regex.compile(_obs_pat_1 + r'\]', regex.DOTALL)

        _open_cur = regex.compile(_obs_pat_1 + r'\{', regex.DOTALL)
        _close_cur = regex.compile(_obs_pat_1 + r'\}', regex.DOTALL)

        _subquery_re = regex.compile(_obs_pat_1 + r'(?P<sq>\{.*)\s*', regex.DOTALL)
        _subquery_balanced_splitter = regex.compile(
            r'(?P<cur>(?<!' + _obs_pat_2 + r')\{(?:(?:' + _obs_pat_2 + r'[{}]|[^{}])++|(?&cur))*(?<!' + _obs_pat_2 + r')\})',
            regex.DOTALL
        )

        _filter_balanced_splitter = regex.compile(
            r'(?P<bra>(?<!' + _obs_pat_2 + r')\[(?:(?:' + _obs_pat_2 + r'[\[\]]|[^\[\]])++|(?&bra))*(?<!' + _obs_pat_2 + r')\])',
            regex.DOTALL
        )
        _filter_re = regex.compile(r'\[(?P<k>[a-z]{1,2}):\s*(?P<v>.+?)\]', regex.DOTALL)

        def __init__(self, phrase: str):
            a_m = self._axis_re.fullmatch(phrase)
            if a_m is None:
                raise ValueError(f'invalid phrase \'{phrase}\'')

            # Axis
            self.axis = a_m.group('a')

            # Order
            self.order = a_m.group('o')

            # Sub-query
            self.subquery_operands = []
            self.subqueries = []
            s_q_m = self._subquery_re.search(phrase, pos=a_m.span('r')[0])
            if s_q_m is not None:
                s_q_g = s_q_m.group('sq')
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
                            raise ValueError(f'missing operator between subqueries \'{last.group(0)}\' and \'{sq.group(0)}\'')
                        elif op not in Ito.QUERY_OPERATORS.keys():
                            raise ValueError(
                                f'invalid subquery operator \'{op}\' between subqueries \'{last.group(0)}\' and \'{sq.group(0)}\'')
                        self.subqueries.append(sq.group(0)[1:-1])
                        last = sq

            # Filter
            self.filter_operands = []
            self.filters = []
            f_start = a_m.span('r')[0]
            f_end = a_m.span('r')[1] if s_q_m is None else s_q_m.span('sq')[0]
            filter_str = phrase[f_start:f_end].strip()
            if len(filter_str) > 0:
                if len([*self._open_bracket.finditer(filter_str)]) != len([*self._close_bracket.finditer(filter_str)]):
                    raise ValueError(f'unbalanced brackets in filter(s) \'{filter_str}\'')
                filts = [*self._filter_balanced_splitter.finditer(filter_str)]
                last = None
                for f in filts:
                    if last is not None:
                        start = last.span(0)[1]
                        stop = f.span(0)[0]
                        op = filter_str[start:stop].strip()
                        if len(op) == 0:
                            raise ValueError(
                                f'missing operator between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
                        elif op not in Ito.QUERY_OPERATORS.keys():
                            raise ValueError(
                                f'invalid filter operator \'{op}\' between filters \'{last.group(0)}\' and \'{f.group(0)}\'')
                        self.filter_operands.append(op)
                        m = self._filter_re.fullmatch(f.group(0))
                        if m is None:
                            raise ValueError(f'invalid filter \'{f.group(0)}\'')
                        self.filters.append({'key': m.group('k'), 'val': m.group('v')})
                        last = f

    @classmethod
    def _axis_order_iter(
            cls,
            itos: typing.Iterable[Ito],
            order: str,
            axis: str
    ) -> typing.Iterable[typing.Tuple[int, Ito]]:
        if order is not None and order not in 'rn':
            raise ValueError(f'invalid axis order \'{order}\'')
        reverse = (order == 'r')

        if axis == '....':
            for i in itos:
                if (r := i.get_root()) is not None:
                    yield 0, r

        elif axis == '...':
            for ito in itos:
                ancestors = []
                cur = ito
                while (cur := cur.parent) is not None:
                    ancestors.append(cur)
                if reverse:
                    ancestors.reverse()
                yield from enumerate(ancestors)

        elif axis == '..':
            for i in itos:
                if (p := i.parent) is not None:
                    yield 0, p

        elif axis == '.':
            yield from enumerate(itos)  # Special case where each ito gets unique enumeration

        elif axis == '-':
            rv = list(collections.OrderedDict.fromkeys(itos))
            if reverse:
                rv.reverse()
            yield from enumerate(rv)

        elif axis == '*':
            for i in itos:
                if reverse:
                    yield from enumerate(i.children[::-1])
                else:
                    yield from enumerate(i.children)

        elif axis == '**':
            for i in itos:
                if reverse:
                    yield from enumerate([*i.walk_descendants()][::-1])
                else:
                    yield from enumerate([*i.walk_descendants()])

        elif axis == '***':
            for i in itos:
                if reverse:
                    yield from enumerate([*(d for d in i.walk_descendants() if len(d.children) == 0)][::-1])
                else:
                    yield from enumerate([*(d for d in i.walk_descendants() if len(d.children) == 0)])

        elif axis == '<<':
            for i in itos:
                if (p := i.parent) is not None:
                    sliced = p.children[0:p.children.index(i)]
                    if reverse:
                        sliced.reverse()
                    yield from enumerate(sliced)

        elif axis == '<':
            for i in itos:
                if (p := i.parent) is not None:
                    idx = p.children.index(i)
                    if idx > 0:
                        yield 0, p.children[idx - 1]

        elif axis == '>':
            for i in itos:
                if (p := i.parent) is not None:
                    idx = p.children.index(i)
                    if idx < len(p.children) - 1:
                        yield 0, p.children[idx + 1]

        elif axis == '>>':
            for i in itos:
                if (p := i.parent) is not None:
                    sliced = p.children[p.children.index(i) + 1:]
                    if reverse:
                        sliced.reverse()
                    yield from enumerate(sliced)

        else:
            raise ValueError(f'invalid axis \'{axis}\'')

    @classmethod
    def _from_phrase(
            cls,
            itos: typing.Iterable[Ito],
            query_step: str,
            values: typing.Dict[str, object] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, Ito], bool]] | None = None
    ) -> typing.Iterable[Ito]:
        qsp = cls._PhraseParse(query_step)

        axis = cls._axis_order_iter(itos, qsp.axis, qsp.order)

        if len(qsp.filters) == 0:
            filt = lambda a: True
        else:
            filt = cls._CombinedFilters(
                [cls._query_step_filter(f['key'], f['val'], values, predicates) for f in qsp.filters],
                qsp.filter_operands
            ).filter

        if len(qsp.subqueries) == 0:
            subq_filt = lambda a: True
        else:
            subq_filt = cls._CombinedSubqueries(
                qsp.subqueries,
                qsp.subquery_operands
            ).filter

        combined_filter = lambda a: filt(a) and subq_filt(a)

        yield from (a[1] for a in filter(combined_filter, axis))

    @classmethod
    def _split_phrases(cls, query: str) -> typing.Iterable[str]:
        rv = ''
        escape = False
        subquery_cnt = 0
        for c in query:
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
                yield rv
                rv = ''
            else:
                rv += c

        if escape:
            raise ValueError('found escape with no succeeding character in \'{query}\'')
        else:
            yield rv

    def find_all(
            self,
            query: str,
            values: typing.Dict[str, typing.Any] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, Ito], bool]] | None = None
    ) -> typing.Iterable[Ito]:
        if query is None or not query.isprintable():
            raise Errors.parameter_neither_none_nor_empty('query')

        current = [self]
        for phrase in self._split_phrases(query):
            if not phrase.isprintable():
                raise ValueError('empty phrase identified; one or more orphan separator(s)')
            current = self._from_phrase(current, phrase, values, predicates)

        yield from current

    def find(
            self,
            query: str,
            values: typing.Dict[str, typing.Any] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, Ito], bool]] | None = None
    ) -> Ito | None:
        return next(self.find_all(query, values, predicates), None)

    # endregion


class ChildItos(collections.abc.Sequence):
    def __init__(self, parent: Ito, *itos: Ito):
        self.__parent = parent
        self.__store: typing.List[Ito] = []
        self.add(*itos)

    # region search & index

    def __bfind_start(self, ito: C) -> int:
        i = bisect.bisect_left(self.__store, ito.start, key=lambda j: j.start)
        if i == len(self.__store) or self.__store[i].start != ito.start:
            return ~i

        return i

    def __bfind_stop(self, ito: C) -> int:
        i = bisect.bisect_right(self.__store, ito.stop, key=lambda j: j.stop)
        if i == len(self.__store) or self.__store[i].stop != ito.stop:
            return ~i

        return i

    def __is_start_lt_prior_stop(self, i: int, ito: Ito) -> bool:
        if i == 0 or len(self.__store) == 0:
            return False

        return ito.start < self.__store[i-1].stop

    def __is_stop_gt_next_start(self, i: int, ito: Ito) -> bool:
        if i == len(self.__store):
            return False

        return ito.stop > self.__store[i].start

    def __ensure_between(self, ito: Ito, i_start: int, i_end: int) -> None:
        if self.__is_start_lt_prior_stop(i_start, ito):
            raise ValueError('parameter \'ito\' overlaps with prior')

        if self.__is_stop_gt_next_start(i_end, ito):
            raise ValueError('parameter \'ito\' overlaps with next')
            
    # endregion

    # region Collection & Set

    def __contains__(self, ito) -> bool:
        return self.__bfind_start(ito) >= 0

    def __iter__(self) -> typing.Iterable[Ito]:
        return self.__store.__iter__()

    def __len__(self) -> int:
        return len(self.__store)

    # endregion

    # region Sequence

    def __getitem__(self, key: int | slice) -> C | typing.List[C]:
        if isinstance(key, int) or isinstance(key, slice):
            return self.__store[key]
        raise Errors.parameter_invalid_type('key', key, int, slice)

    # endregion

    # region Removal

    def __delitem__(self, key: int | slice) -> None:
        if not (isinstance(key, int) or isinstance(key, slice)):
            raise Errors.parameter_invalid_type('key', key, int, slice)
        itos = (self.__store[key],) if isinstance(key, int) else self.__store[key]
        for ito in itos:
            ito._parent = None
        del self.__store[key]

    def remove(self, ito: Ito):
        i = self.__bfind_start(ito)
        if i >= 0 and self.__store[i] is ito:
            self.__delitem__(i)
        else:
            raise ValueError('parameter \'ito\' not found')

    def pop(self, i: int) -> Ito:
        rv = self.__store[i]
        del self[i]
        return rv

    def clear(self):
        self.__delitem__(slice(None))

    # endregion

    # region Add & Update

    def __setitem__(self, key: int | slice, value: Ito | typing.Iterable[Ito]) -> None:
        if isinstance(key, int):
            if not isinstance(value, Ito):
                raise Errors.parameter_invalid_type('value', value, Ito)
            start, stop = Span.from_indices(self, key)
            del self[start]
            self.__ensure_between(value, start, start)
            value._set_parent(self.__parent)
            self.__store.insert(start, value)
            # self.__setitem__(slice(start, start+1), ito)

        elif isinstance(key, slice):
            if isinstance(value, Ito):
                value = [value]
            if isinstance(value, typing.Iterable):
                start, stop = Span.from_indices(self, key.start, key.stop)
                del self[key]
                for ito in value:
                    if not isinstance(ito, Ito):
                        raise Errors.parameter_invalid_type('value', ito, Ito)
                    self.__ensure_between(ito, start, start)
                    ito._set_parent(self.__parent)
                    self.__store.insert(start, ito)
                    start += 1
            else:
                raise Errors.parameter_invalid_type('value', value, Ito, typing.Iterable[Ito])

        else:
            raise Errors.parameter_invalid_type('key', key, int, slice)

    def add(self, *itos: Ito) -> None:
        for ito in itos:
            if ito.parent is not None:
                raise ValueError('parameter \'itos\' has element contained elsewhere')

            i = self.__bfind_start(ito)
            if i >= 0:
                raise ValueError('parameter \'itos\' has overlapping element')

            i = ~i
            self.__ensure_between(ito, i, i)
            ito._set_parent(self.__parent)
            self.__store.insert(i, ito)

    def add_hierarchical(self, *itos: Ito):
        for ito in itos:
            if ito._parent is not None:
                raise ValueError('contained elsewhere...')

            if len(self.__store) == 0:
                ito._set_parent(self.__parent)
                self.__store.append(ito)
                continue

            # do empty span insertions here

            i = self.__bfind_start(ito)
            if i >= 0:
                tmp = self.__store[i]
                if ito.stop <= tmp.stop:
                    tmp.children.add_hierarchical(ito)
                    continue
            else:
                i = ~i
                if i > 0:
                    tmp = self.__store[i-1]
                    if ito.stop <= tmp.stop:
                        tmp.children.add_hierarchical(ito)
                        continue

                    if ito.start < tmp.stop:
                        raise ValueError('Overlaps Case A')

            j = self.__bfind_stop(ito)
            if j >= 0:
                pass  # valid range
            else:
                j = ~j
                if j > 0:
                    tmp = self.__store[j-1]
                    if tmp.start < ito.start < tmp.stop:
                        raise ValueError('Overlaps Case B')

                if j < len(self.__store):
                    tmp = self.__store[j]
                    if ito.start < tmp.start < ito.stop:
                        raise ValueError('Overlaps Case C')

            if i == j:
                self.__store.insert(i, ito)
            else:
                tmp = self[i:j]
                del self[i:j]
                ito.children.add(*tmp)
                self.__store.insert(i, ito)
                ito._set_parent(self.__parent)

    # endregion
