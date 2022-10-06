from __future__ import annotations
import bisect
import collections.abc
import itertools
import types
import typing
import warnings

import regex
from segments.errors import Errors


# Span = typing.Tuple[int, int]
# Span = collections.namedtuple('start', 'stop')
class Span(typing.NamedTuple):
    start: int
    stop: int
        

C = typing.TypeVar('C', bound='Ito')


def slice_indices_to_span(
        basis: int | collections.abc.Sized,
        start: int | None = None,
        stop: int | None = None,
        offset: int = 0
) -> Span:
    if isinstance(basis, int):
        length = basis
    elif isinstance(basis, collections.abc.Sized):
        length = len(basis)
    else:
        raise Errors.parameter_invalid_type('basis', basis, int, collections.abc.Sized)

    if start is None:
        start = offset
    elif not isinstance(start, int):
        raise Errors.parameter_invalid_type('start', start, int, types.NoneType)
    else:
        start = min(length, start) if start >= 0 else max(0, length + start)
        start += offset

    if stop is None:
        stop = length + offset
    elif not isinstance(stop, int):
        raise Errors.parameter_invalid_type('stop', stop, int, types.NoneType)
    else:
        stop = min(length, stop) if stop >= 0 else max(0, length + stop)
        stop += offset

    return Span(start, stop)


class Ito:
    #region ctors

    def __init__(
            self,
            string: str,
            start: int | None = None,
            stop: int | None = None,
            descriptor: str | None = None
    ):
        if string is None:
            raise Errors.parameter_not_none('string')
        elif not isinstance(string, str):
            raise Errors.parameter_invalid_type('string', string, str)
        self._string = string

        self._span = slice_indices_to_span(string, start, stop)

        if descriptor is not None and not isinstance(descriptor, str):
            raise Errors.parameter_invalid_type('descriptor', descriptor, str)
        self.descriptor = descriptor

        self._value_func: typing.Callable[[Ito], typing.Any] | None = None

        self._parent = None
        self._children = ChildItos(self)

    def clone(self,
              start: int | None = None,
              stop: int | None = None,
              descriptor: str | None = None,
              omit_children: bool = False
              ) -> Ito:
        rv = self.__class__(
            self._string,
            self.start if start is None else start,
            self.stop if stop is None else stop,
            self.descriptor if descriptor is None else descriptor
        )

        if self._value_func is not None:
            rv.value_func = self._value_func

        if not omit_children:
            rv.children.add(*(c.clone(omit_children=False) for c in self._children))

        return rv

    def offset(
            self,
            start: int = 0,
            stop: int = 0,
            descriptor: str | None = None
    ) -> Ito:
        if not isinstance(start, int):
            raise Errors.parameter_invalid_type('start', start, int)
        target_start = self.start + start
        if not 0 <= target_start <= len(self._string):
            warnings.warn(
                f'.offset called with parameter \'start\' = {start} for ito with .span = {self.span}.',
                stacklevel=2
            )

        if not isinstance(stop, int):
            raise Errors.parameter_invalid_type('stop', stop, int)
        target_stop = self.stop + stop
        if not 0 <= target_stop <= len(self._string):
            warnings.warn(
                f'.offset called with parameter \'stop\' = {stop} for ito with .span = {self.span}.',
                stacklevel=2
            )

        return self.clone(
            target_start,
            target_stop,
            self.descriptor if descriptor is None else descriptor
        )

    def slice(self, start: int = None, stop: int = None, descriptor: str = None) -> Ito:
        return self.clone(
            *slice_indices_to_span(self, start, stop, self.start),
            self.descriptor if descriptor is None else descriptor
        )

    @classmethod
    def from_match(cls,
                   match: regex.Match,
                   group: str | int = 0,
                   descriptor: str = None
                   ) -> C:
        if match is None:
            raise Errors.parameter_not_none('match')
        elif not isinstance(match, regex.Match):
            raise Errors.parameter_invalid_type('match', match, regex.Match)

        if group is None:
            raise Errors.parameter_not_none('group')

        return cls(match.string, *match.span(group), descriptor=descriptor)

    @classmethod
    def _gf(cls,
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

    def from_match_ex(
            self,
            match: regex.Match,
            descriptor_func: typing.Callable[[regex.Match, str], str] = lambda ito, match, group: group,
            group_filter: typing.Iterable[str] | typing.Callable[[regex.Match, str], bool] | None = None
    ) -> typing.Iterable[C]:
        path_stack: typing.List[Ito] = []
        rv: typing.List[Ito] = []
        gf = self._gf(group_filter)
        filtered_gns = (gn for gn in match.re.groupindex.keys() if gf(match, gn))
        span_gns = ((span, gn) for gn in filtered_gns for span in match.spans(gn))
        for span, gn in sorted(span_gns, key=lambda val: (val[0][0], -val[0][1])):
            ito = Ito(match.string, *span, descriptor=descriptor_func(match, gn))
            while len(path_stack) > 0 and (ito.start < path_stack[-1].start or ito.stop > path_stack[-1].stop):
                path_stack.pop()
            if len(path_stack) == 0:
                rv.append(ito)
            else:
                path_stack[-1].children.add(ito)

            path_stack.append(ito)

        yield from rv

    @classmethod
    def from_spans(cls, string: str, *spans: Span, descriptor: str | None = None) -> typing.List[C]:
        return [cls(string, *s, descriptor=descriptor) for s in spans]

    @classmethod
    def from_substrings(
            cls,
            string: str,
            *substrings: str,
            descriptor: str | None = None
    ) -> typing.Iterable[C]:
        """
        :param string:
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
        :param descriptor:
        :return:
        """
        i = 0
        for sub in substrings:
            i = string.index(sub, i)
            k = i + len(sub)
            yield cls(string, i, k, descriptor)
            i = k

    #endregion

    #region properties

    @property
    def string(self) -> str:
        return self._string

    @property
    def span(self) -> Span:
        return self._span

    @property
    def start(self) -> int:
        return self._span[0]

    @property
    def stop(self) -> int:
        return self._span[1]

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

    @property
    def value_func(self) -> typing.Callable[[Ito], typing.Any]:
        return self._value_func

    @value_func.setter
    def value_func(self, f: typing.Callable[[Ito], typing.Any]) -> None:
        if f is None:
            delattr(self, '__value__')
        else:
            setattr(self, '__value__', f.__get__(self))
        self._value_func = f

    #endregion

    #region __x__ methods
        
    def __repr__(self) -> str:
        # TODO : Add children to repr str?
        return f'segments.Ito({self._string.__repr__()}, {self.start}, {self.stop}, {self.descriptor.__repr__()})'

    def __str__(self) -> str:
        return self._string[slice(*self.span)]

    def __value__(self) -> typing.Any:
        return self.__str__()

    def __len__(self) -> int:
        return self.stop - self.start

    def __getitem__(self, key: int | slice) -> str:
        if isinstance(key, int):
            span = slice_indices_to_span(self, key, None, self.start)
            return self._string[span.start]
        
        if isinstance(key, slice):
            span = slice_indices_to_span(self, key.start, key.stop, self.start)
            return self._string[slice(*span)]
        
        raise Errors.parameter_invalid_type('key', key, int, slice)
        
    #endregion

    #region traversal

    def get_root(self) -> C | None:
        rv = self.parent

        while rv is not None:
            rv = rv.parent

        return rv

    def walk_descendants_levels(self, start: int = 0) -> typing.Iterable[typing.Tuple[int, C]]:
        for child in self.children:
            yield start, child
            yield from child.walk_descendants_levels(start+1)

    def walk_descendants(self) -> typing.Iterable[C]:
        yield from (ito for lvl, ito in self.walk_descendants_levels())

    #endregion

    #region combinatorics

    @classmethod
    def join(cls, *itos: C, descriptor: str | None = None) -> C:
        it_str, it_start, it_stop, it_children = itertools.tee(itos, 4)

        strs = set(ito.string for ito in it_str)
        if len(strs) > 1:
            raise ValueError(f'parameter \'{itos}\' have differing values for .string')

        start = min(ito.start for ito in it_start)
        stop = max(ito.stop for ito in it_stop)
        rv = Ito(strs.pop(), start, stop, descriptor)

        children = itertools.chain.from_iterable(ito.children for ito in itos)
        rv.children.add(*(c.clone() for c in children))

        return rv

    #endregion

    #region regex equivalence methods

    def regex_match(self, re: regex.Pattern) -> regex.Match:
        return re.match(self.string, *self.span)

    def regex_search(self, re: regex.Pattern) -> regex.Match:
        return re.search(self.string, *self.span)

    def regex_finditer(self, re: regex.Pattern) -> typing.Iterable[regex.Match]:
        return re.finditer(self.string, *self.span)

    #endregion

    #region str equivalence methods

    def str_count(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.count(sub, *slice_indices_to_span(self, start, end, self.start))

    def str_endswith(self, suffix: str | typing.Tuple[str, ...], start: int | None = None, end: int | None = None) -> bool:
        if suffix is None:
            raise Errors.parameter_invalid_type('suffix', suffix, str, typing.Tuple[str, ...])
        elif start is not None and start > len(self):  # Weird rule, but this is how python str works
            return False
        else:
            norms = slice_indices_to_span(self, start, end, self.start)
            return self._string.endswith(suffix, *norms)

    def str_find(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.find(sub, *slice_indices_to_span(self, start, end, self.start))

    def str_index(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.index(sub, *slice_indices_to_span(self, start, end, self.start))

    #region 'is' predicates

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

    #endregion

    def str_lstrip(self, chars: str | None) -> Ito:
        pass

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

    def str_removeprefix(self, prefix: str) -> Ito:
        if self.str_startswith(prefix):
            return self.clone(len(prefix))
        else:
            return self.clone()

    def str_removesuffix(self, suffix: str) -> Ito:
        if self.str_endswith(suffix):
            return self.clone(stop=-len(suffix))
        else:
            return self.clone()
        
    def str_rfind(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.rfind(sub, *slice_indices_to_span(self, start, end, self.start))

    def str_rindex(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.rindex(sub, *slice_indices_to_span(self, start, end, self.start))
    
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
                return self.clone(stop=i), self.clone(i, i+len(sep)), self.clone(i+len(sep))    

    def str_rsplit(self, sep: str = None, maxsplit: int = -1) -> typing.List[Ito]:
        if sep is None:
            return self.str_split(sep, maxsplit)  # rsplit has same effect as split when sep is None
        elif sep == '':
            raise ValueError('empty separator')
        else:
            pass
        
    def str_rstrip(self, chars: str | None) -> typing.List[Ito]:
        pass

    def str_split(self, sep: str = None, maxsplit: int = -1) -> typing.List[Ito]:
        # TODO : handle maxsplit
        if sep is None:
            # TODO : improve algorithm : split on consecutive runs of whitespace
            return [*Ito.from_substrings(self.string, *self.__str__().split())]
        elif sep == '':
            raise ValueError('empty separator')
        else:
            rv: typing.List[Ito] = []
            i = self.start
            while (j := self._string.find(sep, i, self.stop)) >= 0:
                rv.append(self.clone(i, j))
                i = j + len(sep)
            if i <= self.stop:
                rv.append(self.clone(i))
            return rv
        
    def str_splitlines(self, keepends: bool = False) -> Typing.List[Ito]:
        pass

    def str_startswith(
            self,
            prefix: str | typing.Tuple[str, ...],
            start: int | None = None,
            end: int | None = None
    ) -> bool:
        if prefix is None:
            raise Errors.parameter_invalid_type('prefix', prefix, str, typing.Tuple[str, ...])
        elif start is not None and start > len(self):  # Weird rule, but this is how python str works
            return False
        else:
            span = slice_indices_to_span(self, start, end, self.start)
            return self._string.startswith(prefix, *span)
        
    def str_strip(self, chars: str | None = None) -> Ito:
        pass

    #endregion


class ChildItos(collections.abc.Sequence):
    def __init__(self, parent: Ito, *itos: Ito):
        self.__parent = parent
        self.__store: typing.List[Ito] = []
        self.add(*itos)

    #region search & index

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
    #endregion

    #region Collection & Set

    def __contains__(self, ito) -> bool:
        return self.__bfind_start(ito) >= 0

    def __iter__(self) -> typing.Iterable[Ito]:
        return self.__store.__iter__()

    def __len__(self) -> int:
        return len(self.__store)

    #endregion

    #region Sequence

    def __getitem__(self, key: int | slice) -> C | typing.List[C]:
        if isinstance(key, int) or isinstance(key, slice):
            return self.__store[key]
        raise Errors.parameter_invalid_type('key', key, int, slice)

    #endregion

    #region Removal

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

    #endregion

    #region Add & Update

    def __setitem__(self, key: int | slice, value: Ito | typing.Iterable[Ito]) -> None:
        if isinstance(key, int):
            if not isinstance(value, Ito):
                raise Errors.parameter_invalid_type('value', value, Ito)
            start, stop = slice_indices_to_span(self, key)
            del self[start]
            self.__ensure_between(value, start, start)
            value._set_parent(self.__parent)
            self.__store.insert(start, value)
            # self.__setitem__(slice(start, start+1), ito)

        elif isinstance(key, slice):
            if isinstance(value, Ito):
                value = [value]
            if isinstance(value, typing.Iterable):
                start, stop = slice_indices_to_span(self, key.start, key.stop)
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
