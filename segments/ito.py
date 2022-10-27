from __future__ import annotations
import bisect
import collections.abc
import dataclasses
import inspect
import itertools
import json
import pickle
import types
import typing

import regex

import segments.query
from segments import Infix
from segments.span import Span
from segments.errors import Errors


class Types:

    C_ITO = typing.TypeVar('C_ITO', bound='Ito')
    C_SQ_ITOS = typing.Sequence[C_ITO]
    C_IT_ITOS = typing.Iterable[C_ITO]

    F_ITO_2_VAL = typing.Callable[[C_ITO], typing.Any]
    F_ITO_2_ITOR = typing.Callable[[C_ITO], 'Itorator']
    F_ITO_2_SQ_ITOS = typing.Callable[[C_ITO], C_SQ_ITOS]
    F_ITO_2_IT_ITOS = typing.Callable[[C_ITO], C_IT_ITOS]

    C_GK = int | str
    F_ITO_M_GK_2_B = typing.Callable[[C_ITO, regex.Match, int | str], bool]
    F_ITO_M_GK_2_DESC = typing.Callable[[C_ITO | None, regex.Match, int | str], str]

    class C_EITO(typing.NamedTuple):
        index: int
        ito: segments.Types.C_ITO

    C_IT_EITOS = typing.Iterable[C_EITO]
    C_VALUES = typing.Dict[str, typing.Any] | None
    C_PREDICATES = typing.Dict[str, typing.Callable[[C_EITO], bool]] | None
    F_EITO_V_P_2_B = typing.Callable[[C_EITO, C_VALUES, C_PREDICATES], bool]

    @dataclasses.dataclass(init=False)
    class TypeSig:
        ret_val: type = dataclasses.field(default_factory=lambda: [types.NoneType])
        params: typing.List[typing.Type] = dataclasses.field(default_factory=lambda: [])

        def __init__(self, rv: type, *params: type):
            self.ret_val = rv
            self.params = [*params]

    @classmethod
    def type_matches_annotation(cls, _type: typing.Type, annotation: typing.Type) -> bool:
        if annotation == inspect._empty:
            return True

        if _type == annotation:
            return True

        origin = typing.get_origin(annotation)
        if origin is types.UnionType:
            return _type in typing.get_args(annotation)
        elif issubclass(_type, annotation):
            return True

        return False

    @classmethod
    def is_callable(cls, func: typing.Any, ts: TypeSig) -> bool:
        if not isinstance(func, typing.Callable):
            return False

        func_sig = inspect.signature(func)
        if not cls.type_matches_annotation(ts.ret_val, func_sig.return_annotation):
            return False

        if len(ts.params) != len(func_sig.parameters):
            return False

        if not all(
                cls.type_matches_annotation(tsp, fsp.annotation) for tsp, fsp in zip(ts.params, func_sig.parameters.values())):
            return False

        return True


#class Operators
nuco = Infix(lambda x, y: y if x is None else x)


class Ito:
    # region ctors & clone

    def __init__(
            self,
            src: str | Ito,
            start: int | None = None,
            stop: int | None = None,
            desc: str | None = None
    ):
        if isinstance(src, str):
            self._string = src
            self._span = Span.from_indices(src, start, stop)
            
        elif isinstance(src, Ito):
            self._string = src.string
            self._span = Span.from_indices(src, start, stop).offset(src.start)
        
        else:
            raise Errors.parameter_invalid_type('src', src, str, Ito)

        if desc is not None and not isinstance(desc, str):
            raise Errors.parameter_invalid_type('desc', desc, str)
        self.desc = desc

        self._value_func: Types.F_ITO_2_VAL | None = None

        self._parent = None
        self._children = ChildItos(self)

    @classmethod
    def from_match(cls,
                   match: regex.Match,
                   group: str | int = 0,
                   desc: str = None
                   ) -> Types.C_ITO:
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
            typing.Callable[[Types.C_ITO, regex.Match, str], bool],
            types.NoneType)

    @classmethod
    def from_match_ex(
            cls,
            match: regex.Match,
            desc_func: Types.F_ITO_M_GK_2_DESC = lambda ito, match, group: group,
            group_filter: typing.Iterable[str] | typing.Callable[[regex.Match, str], bool] | None = None
    ) -> typing.Iterable[Types.C_ITO]:
        path_stack: typing.List[Types.C_ITO] = []
        match_itos: typing.List[Types.C_ITO] = []
        filtered_gns = (gn for gn in match.re.groupindex.keys() if cls._group_filter(group_filter)(match, gn))
        span_gns = ((span, gn) for gn in filtered_gns for span in match.spans(gn))
        for span, gn in sorted(span_gns, key=lambda val: (val[0][0], -val[0][1])):
            ito = cls(match.string, *span, desc_func(None, match, gn))
            while len(path_stack) > 0 and (ito.start < path_stack[-1].start or ito.stop > path_stack[-1].stop):
                path_stack.pop()
            if len(path_stack) == 0:
                match_itos.append(ito)
            else:
                path_stack[-1].children.add(ito)

            path_stack.append(ito)

        yield from match_itos

    @classmethod
    def from_re(
            cls,
            re: regex.Pattern,
            src: str | Types.C_ITO,
            desc_func: Types.F_ITO_M_GK_2_DESC = lambda ito, match, group: group,
            group_filter: typing.Iterable[str] | typing.Callable[[regex.Match, str], bool] | None = None,
            limit: int | None = None,
    ) -> typing.Iterable[Types.C_ITO]:
        if isinstance(src, str):
            s = src
            span = Span.from_indices(s)
        elif isinstance(src, Ito):
            s = src.string
            span = src.span
        else:
            raise Errors.parameter_invalid_type('src', src, str, Ito)
        for count, m in enumerate(re.finditer(s, *span), 1):
            yield from cls.from_match_ex(m, desc_func, group_filter)
            if limit is not None and count >= limit:
                break

    @classmethod
    def from_spans(cls, src: str | Types.C_ITO, *spans: Span, desc: str | None = None) -> typing.Iterable[Types.C_ITO]:
        """Generate Itos from spans
        
        Args:
            src: a str or Ito to use as the basis
            spans: one or more spans within the basis
            desc: a descriptor for the generated Itos
            
        Yields:
            Itos; stream ordering will match that of spans; if spans overlap, so will the resulting Itos
        """
        yield from (cls(src, *s, desc=desc) for s in spans)
        
    @classmethod
    def from_gaps(cls, src: str | Types.C_ITO, *gaps: Span, desc: str | None = None) -> typing.Iterable[Types.C_ITO]:
        """Generate Itos from gaps (negative space)
        
        Args:
            src: a str or Ito to use as the basis
            gaps: one or more Spans that resulting Itos will exclude
            desc: a descriptor for the generated Itos
            
        Yields:
            Itos; stream ordering will be left to right; overlapping spans are allowed
        """
        stop = 0
        for gap in sorted(gaps):
            if gap.start > stop:
                yield cls(src, stop, gap.start, desc=desc)
            stop = gap.stop
        if stop < len(src):
            yield cls(src, stop, desc=desc)

    @classmethod
    def from_substrings(
            cls,
            src: str | Ito,
            *substrings: str,
            desc: str | None = None
    ) -> typing.Iterable[Types.C_ITO]:
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
              ) -> Types.C_ITO:
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

    def _set_string(self, string: str) -> None:
        if len(string) < self.start <= self.stop:
            raise ValueError(f'parameter \'string\' does not contain .span {self.span}')
        self._string = string
        for c in self.walk_descendants():
            c._string = string
    
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

    def _set_parent(self, parent: Types.C_ITO) -> None:
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
    def value_func(self) -> Types.F_ITO_2_VAL | None:
        return self._value_func

    @value_func.setter
    def value_func(self, f: Types.F_ITO_2_VAL | None) -> None:
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
        rv = pickle.loads(pickle_str)
        rv._string = ito_str
        return rv

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_parent']
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
                'span': o._span,
                'desc': o.desc,
                'children': [self.default(c) for c in o.children]
            }

    class JsonEncoder(json.JSONEncoder):
        def default(self, o: typing.Any) -> typing.Dict:
            return {
                '__type__': 'typing.Tuple[str, Ito]',
                'string': o.string,
                'ito': Ito.JsonEncoderStringless().default(o)
            }

    @classmethod
    def json_decoder_stringless(cls, obj: typing.Dict) -> Types.C_ITO | typing.Dict:
        if (t := obj.get('__type__')) is not None and t == 'Ito':
            rv = cls('', desc=obj['desc'])
            rv._span = Span(*obj['span'])
            rv.children.add(*obj['children'])
            return rv
        else:
            return obj

    @classmethod
    def json_decoder(cls, obj: typing.Dict) -> Types.C_ITO | typing.Dict:
        if (t := obj.get('__type__')) is not None:
            if t == 'typing.Tuple[str, Ito]':
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
    
    def __key(self) -> typing.Tuple[Span, Types.F_ITO_2_VAL | None, str | None, str]:
        """Inverse ordered by comparison cost, i.e., cheap-to-compare items at start of tuple
        
        Returns:
            Hashable tuple
        """
        return self._span, self.value_func, self.desc, self._string
    
    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, o: typing.Any) -> bool:
        """Itos are equal if they have equal:
        
            1) type (differing polymorphic instances are considered not equal)
            2) .string & .desc values (using string equality not identity)
            3) .span values
            4) .value_func values
        
        Collection memberships are not considered, i.e., .parent and .children and not considered
        
        Args:
            o: object to be compared
        
        Returns:
            True or False
        """
        if self is o:
            return True
        
        if not isinstance(o, type(self)):
            return False
        
        return self.__key() == o.__key()
    
    def __iter__(self) -> typing.Iterable[str]:
        for i in range(*self.span):
            yield self._string[i]

    def __ne__(self, o: typing.Any) -> bool:
        return not self.__eq__(o)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._string.__repr__()}, {self.start}, {self.stop}, {self.desc.__repr__()})'

    def __str__(self) -> str:
        return self._string[slice(*self.span)]

    def __len__(self) -> int:
        return self.stop - self.start

    def __getitem__(self, key: int | slice | None) -> Types.C_ITO:
        if isinstance(key, int):
            if 0 <= key < len(self):
                span = Span.from_indices(self, key, key + 1).offset(self.start)
            elif -len(self) <= key < 0:
                s = self.stop + key - 1
                span = Span.from_indices(self, s, s + 1).offset(self.start)
            else:
                raise IndexError('Ito index out of range')
                
        elif isinstance(key, slice):
            if key.step is None or key.step == 1:
                span = Span.from_indices(self, key.start, key.stop).offset(self.start)
            else:
                raise IndexError('step values other than None or 1 are not supported')
                
        else:
            raise Errors.parameter_invalid_type('key', key, int, slice)

        if self.span == span:
            return self  # Replicate Python's str[:] behavior, which returns self ref
                                            
        return self.clone(*span)

    # endregion

    # region combinatorics

    @classmethod
    def adopt(cls, *itos: Types.C_ITO, desc: str | None = None) -> Types.C_ITO:
        """Creates a parent for a sequence of Itos

        Args:
            *itos: a sequence of itos that have
                a) identical values for .string
                b) non-overlapping edges
            desc: a descriptor for the parent ito

        Returns:
            An Ito whose .span matches the min .start and max .stop of the
            input sequence, and to whose .children clones of the input sequence
            have been hierarchically added

        """
        it_str, it_start, it_stop, it_children = itertools.tee(itos, 4)

        strs = set(ito.string for ito in it_str)
        if len(strs) > 1:
            raise ValueError(f'parameter \'{itos}\' have differing values for .string')

        start = min(ito.start for ito in it_start)
        stop = max(ito.stop for ito in it_stop)
        rv = cls(strs.pop(), start, stop, desc)

        children: typing.Iterable[Types.C_ITO] = itertools.chain.from_iterable(ito.children for ito in itos)
        rv.children.add_hierarchical(*(c.clone() for c in children))

        return rv

    def split_iter(
            self,
            re: regex.Pattern,
            desc: str | None = None,
            max_split: int = 0,
            keep_seps: bool = False
    ) -> typing.Iterable[Types.C_ITO]:
        count = 0
        i = self.start
        for m in self.regex_finditer(re):
            if max_split != 0 and max_split >= count:
                break
            span = Span(*m.span(0))
            stop = span.stop if keep_seps else span.start
            yield self.clone(i, stop, desc)
            i = span.stop

        if i < self.stop:
            yield self.clone(i, desc=desc)
        elif i == self.stop:
            yield self.clone(i, i, desc)

    def split(
            self,
            re: regex.Pattern,
            desc: str | None = None,
            max_split: int = 0,
            keep_seps: bool = False
    ) -> typing.List[Types.C_ITO]:
        return [*self.split_iter(re, desc, max_split, keep_seps)]

    # endregion

    # region regex equivalence methods

    def regex_search(
            self,
            re: regex.Pattern,
            concurrent: bool | None = None,
            timeout: float | None = None
    ) -> regex.Match:
        return re.search(
            self.string,
            *self.span,
            concurrent=concurrent,
            timeout=timeout)

    def regex_match(
            self,
            re: regex.Pattern,
            concurrent: bool | None = None,
            timeout: float | None = None
    ) -> regex.Match:
        return re.match(
            self.string,
            *self.span,
            concurrent=concurrent,
            timeout=timeout)

    def regex_fullmatch(
            self,
            re: regex.Pattern,
            concurrent: bool | None = None,
            timeout: float | None = None
    ) -> regex.Match:
        return re.fullmatch(
            self.string,
            *self.span,
            concurrent=concurrent,
            timeout=timeout)

    def regex_split(self, re: regex.Pattern, maxsplit: int = 0) -> typing.List[str]:
        return [*self.regex_splititer(re, maxsplit)]

    def regex_splititer(self, re: regex.Pattern, maxsplit: int = 0) -> typing.Iterable[str]:
        yield from (str(i) for i in self.split_iter(re, max_split=maxsplit, keep_seps=False))

    def regex_findall(
            self,
            re: regex.Pattern,
            overlapped: bool = False,
            concurrent: bool | None = None,
            timeout: float | None = None
    ) -> typing.List[regex.Match]:
        return re.findall(
            self.string,
            *self.span,
            overlapped=overlapped,
            concurrent=concurrent,
            timeout=timeout)

    def regex_finditer(
            self,
            re: regex.Pattern,
            overlapped: bool = False,
            concurrent: bool | None = None,
            timeout: float | None = None
    ) -> typing.Iterable[regex.Match]:
        return re.finditer(
            self.string,
            *self.span,
            overlapped=overlapped,
            concurrent=concurrent,
            timeout=timeout)

    # endregion

    # region str equivalence methods

    def str_count(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.count(sub, *Span.from_indices(self, start, end).offset(self.start))

    # region endswtih, startswtih
        
    def str_endswith(
            self,
            suffix: str | typing.Tuple[str, ...],
            start: int | None = None,
            end: int | None = None
    ) -> bool:
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
        norms = Span.from_indices(self, start, end).offset(self.start)
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
        norms = Span.from_indices(self, start, end).offset(self.start)
        return self._string.startswith(prefix, *norms)

    # endregion

    # region find, index, rfind, rindex
   
    def str_find(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.find(sub, *Span.from_indices(self, start, end).offset(self.start)) - self.start

    def str_index(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.index(sub, *Span.from_indices(self, start, end).offset(self.start)) - self.start
    
    def str_rfind(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.rfind(sub, *Span.from_indices(self, start, end).offset(self.start)) - self.start

    def str_rindex(self, sub: str, start: int | None = None, end: int | None = None) -> int:
        return self._string.rindex(sub, *Span.from_indices(self, start, end).offset(self.start)) - self.start

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
        return str(self).isidentifier()

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
        return str(self).istitle()

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

    def str_lstrip(self, chars: str | None = None) -> Types.C_ITO:
        f_c_in = self.__f_c_in(chars)
        i = self.start
        while i < self.stop and f_c_in(i):
            i += 1
        return self.clone(i)

    def str_rstrip(self, chars: str | None = None) -> Types.C_ITO:
        f_c_in = self.__f_c_in(chars)
        i = self.stop - 1
        while i >= 0 and f_c_in(i):
            i -= 1

        return self.clone(stop=i+1)

    def str_strip(self, chars: str | None = None) -> Types.C_ITO:
        return self.str_lstrip(chars).str_rstrip(chars)

    # endregion

    # region partition and split methods

    def str_partition(self, sep) -> typing.Tuple[Types.C_ITO, Types.C_ITO, Types.C_ITO]:
        if sep is None:
            raise ValueError('must be str, not NoneType')
        elif sep == '':
            raise ValueError('empty separator')
        else:
            i = self.str_find(sep)
            if i < 0:
                return self.clone(), self.clone(self.stop), self.clone(self.stop)
            else:
                j = i + self.start
                k = j + len(sep)
                return self.clone(stop=j), self.clone(j, k), self.clone(k)

    def str_rpartition(self, sep) -> typing.Tuple[Types.C_ITO, Types.C_ITO, Types.C_ITO]:
        if sep is None:
            raise ValueError('must be str, not NoneType')
        elif sep == '':
            raise ValueError('empty separator')
        else:
            i = self.str_rfind(sep)
            if i < 0:
                return self.clone(self.stop), self.clone(self.stop), self.clone()
            else:
                j = i + self.start
                k = j + len(sep)
                return self.clone(stop=j), self.clone(j, k), self.clone(k)

    def __nearest_non_ws_sub(self, start: int, reverse: bool = False) -> Types.C_ITO | None:
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
            c = str(self[i])
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

    def str_rsplit(self, sep: str = None, maxsplit: int = -1) -> typing.List[Types.C_ITO]:
        if sep is None:
            rv: typing.List[Types.C_ITO] = []
            if self._string == '':
                return rv

            i = self.stop - 1
            rv: typing.List[Types.C_ITO] = []
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

            rv: typing.List[Types.C_ITO] = []
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

    def str_split(self, sep: str = None, maxsplit: int = -1) -> typing.List[Types.C_ITO]:
        if sep is None:
            rv: typing.List[Types.C_ITO] = []
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

            rv: typing.List[Types.C_ITO] = []
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

    def str_splitlines(self, desc: str | None = None, keepends: bool = False) -> typing.List[Types.C_ITO]:
        rv = [*self.split_iter(self._splitlines_re, desc, 0, keepends)]

        if len(rv) == 0:
            return rv
        if len(rv[-1]) == 0:
            rv.pop(-1)
        return rv

    # endregion

    # region removeprefix, removesuffix

    def str_removeprefix(self, prefix: str) -> Types.C_ITO:
        if self.str_startswith(prefix):
            return self.__class__(self, len(prefix), desc=self.desc)
        else:
            return self.clone()

    def str_removesuffix(self, suffix: str) -> Types.C_ITO:
        if self.str_endswith(suffix):
            return self.__class__(self, stop=-len(suffix), desc=self.desc)
        else:
            return self.clone()
        
    # endregion

    # endregion

    # region traversal

    def get_root(self) -> Types.C_ITO | None:
        rv = self
        while (parent := rv.parent) is not None:
            rv = parent
        return rv

    def walk_descendants_levels(self, start: int = 0, reverse: bool = False) -> Types.C_IT_EITOS:
        for child in reversed(self.children) if reverse else self.children:
            if not reverse:
                yield Types.C_EITO(start, child)
            yield from child.walk_descendants_levels(start + 1, reverse)
            if reverse:
                yield Types.C_EITO(start, child)

    def walk_descendants(self, reverse: bool = False) -> Types.C_IT_EITOS:
        yield from (ito for lvl, ito in self.walk_descendants_levels(reverse=reverse))

    # endregion

    # region query

    def find(
            self,
            query: str,
            values: typing.Dict[str, typing.Any] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, Types.C_ITO], bool]] | None = None
    ) -> Types.C_ITO | None:
        return next(self.find_all(query, values, predicates), None)

    def find_all(
            self,
            query: str,
            values: typing.Dict[str, typing.Any] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, Types.C_ITO], bool]] | None = None
    ) -> typing.Iterable[Types.C_ITO]:
        query = segments.query.compile(query)
        yield from query.find_all(self, values, predicates)

    # endregion


class ChildItos(collections.abc.Sequence):
    def __init__(self, parent: Types.C_ITO, *itos: Types.C_ITO):
        self.__parent = parent
        self.__store: typing.List[Types.C_ITO] = []
        self.add(*itos)

    # region search & index

    def __bfind_start(self, ito: Types.C_ITO) -> int:
        i = bisect.bisect_left(self.__store, ito.start, key=lambda j: j.start)
        if i == len(self.__store) or self.__store[i].start != ito.start:
            return ~i

        return i

    def __bfind_stop(self, ito: Types.C_ITO) -> int:
        i = bisect.bisect_right(self.__store, ito.stop, key=lambda j: j.stop)
        if i == len(self.__store) or self.__store[i].stop != ito.stop:
            return ~i

        return i

    def __is_start_lt_prior_stop(self, i: int, ito: Types.C_ITO) -> bool:
        if i == 0 or len(self.__store) == 0:
            return False

        return ito.start < self.__store[i-1].stop

    def __is_stop_gt_next_start(self, i: int, ito: Types.C_ITO) -> bool:
        if i == len(self.__store):
            return False

        return ito.stop > self.__store[i].start

    def __ensure_between(self, ito: Types.C_ITO, i_start: int, i_end: int) -> None:
        if self.__is_start_lt_prior_stop(i_start, ito):
            raise ValueError('parameter \'ito\' overlaps with prior')

        if self.__is_stop_gt_next_start(i_end, ito):
            raise ValueError('parameter \'ito\' overlaps with next')
            
    # endregion

    # region Collection & Set

    def __contains__(self, ito) -> bool:
        return self.__bfind_start(ito) >= 0

    def __iter__(self) -> typing.Iterable[Types.C_ITO]:
        return self.__store.__iter__()

    def __len__(self) -> int:
        return len(self.__store)

    # endregion

    # region Sequence

    def __getitem__(self, key: int | slice) -> Types.C_ITO | typing.List[Types.C_ITO]:
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

    def remove(self, ito: Types.C_ITO):
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

    def __setitem__(self, key: int | slice, value: Types.C_ITO | typing.Iterable[Types.C_ITO]) -> None:
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
                raise Errors.parameter_invalid_type('value', value, Ito, typing.Iterable[Types.C_ITO])

        else:
            raise Errors.parameter_invalid_type('key', key, int, slice)

    def add(self, *itos: Types.C_ITO) -> None:
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

    def add_hierarchical(self, *itos: Types.C_ITO):
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
