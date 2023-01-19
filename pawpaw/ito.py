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

import pawpaw.query
from pawpaw import Infix
from pawpaw.span import Span
from pawpaw.errors import Errors
from .util import find_escapes


class Types:
    C_ITO = typing.TypeVar('C_ITO', bound='Ito')
    C_SQ_ITOS = typing.Sequence[C_ITO]
    C_IT_ITOS = typing.Iterable[C_ITO]

    F_ITO_2_B = typing.Callable[[C_ITO], bool]
    F_ITO_2_VAL = typing.Callable[[C_ITO], typing.Any]
    F_ITO_2_DESC = typing.Callable[[C_ITO], str]
    F_ITO_2_ITOR = typing.Callable[[C_ITO], 'Itorator']
    F_ITO_2_SQ_ITOS = typing.Callable[[C_ITO], C_SQ_ITOS]
    F_ITO_2_IT_ITOS = typing.Callable[[C_ITO], C_IT_ITOS]

    C_GK = int | str
    F_M_GK_2_DESC = typing.Callable[[regex.Match, C_GK], str]

    F_ITO_M_GK_2_B = typing.Callable[[C_ITO | None, regex.Match, C_GK], bool]
    F_ITO_M_GK_2_DESC = typing.Callable[[C_ITO | None, regex.Match, C_GK], str]
    F_M_GK_2_B = typing.Callable[[regex.Match, C_GK], bool]

    class C_BITO(typing.NamedTuple):
        tf: bool
        ito: pawpaw.Types.C_ITO
    C_IT_BITOS = typing.Iterable[C_BITO]
    F_ITOS_2_BITOS = typing.Callable[[C_IT_ITOS], C_IT_BITOS]

    class C_EITO(typing.NamedTuple):
        index: int
        ito: pawpaw.Types.C_ITO
    C_IT_EITOS = typing.Iterable[C_EITO]

    C_VALUES = typing.Dict[str, typing.Any] | None
    C_PREDICATES = typing.Dict[str, typing.Callable[[C_EITO], bool]] | None
    F_EITO_V_P_2_B = typing.Callable[[C_EITO, C_VALUES, C_PREDICATES], bool]

    C_PATH = str | C_ITO

    @classmethod
    def type_matches_annotation(cls, _type: typing.Type, annotation: typing.Type) -> bool:
        if annotation == inspect._empty:
            return True

        if _type == annotation:
            return True

        origin = typing.get_origin(annotation)
        if origin is types.UnionType:
            return _type in typing.get_args(annotation)

        if isinstance(_type, typing.TypeVar):
            if getattr(typing, 'reveal_type', None) is None:  # Python < 3.11 check
                return True  # Can't reveal type in < 3.11 versions

            _type = typing.reveal_type(_type)

        if issubclass(_type, annotation):
            return True

        return False

    @classmethod
    def is_callable(cls, func: typing.Any, type_sig: typing.Callable) -> bool:
        if not isinstance(func, typing.Callable):
            return False

        ts_params, ts_rv = typing.get_args(type_sig)
        
        func_sig = inspect.signature(func)
        if not cls.type_matches_annotation(ts_rv, func_sig.return_annotation):
            return False

        if len(ts_params) != len(func_sig.parameters):
            return False

        if not all(
                cls.type_matches_annotation(tsp, fsp.annotation) for tsp, fsp in zip(ts_params, func_sig.parameters.values())):
            return False

        return True

    @classmethod
    def is_desc_func(cls, func: typing.Callable) -> bool:
        if not isinstance(func, typing.Callable):
            return False

        sig = inspect.signature(func)
        if not cls.type_matches_annotation(str, sig.return_annotation):
            return False

        return True

    @classmethod
    def is_lambda(cls, func: typing.Callable):
        return type(func) is types.LambdaType and func.__name__ == '<lambda>'

    @classmethod
    def invoke_func(cls, func: typing.Any, *vals: typing.Any) -> typing.Any:
        """Wire and fire

        Args:
            func:
            *vals:

        Returns:
            Invokes func and returns its return value
        """

        if cls.is_lambda(func):
            return func(*vals)  # No type hints on lamdbas, so this is the best we can do

        unpaired: typing.List[typing.Any] = list(vals)

        arg_spec = inspect.getfullargspec(func)
        del arg_spec.annotations['return']

        p_args: typing.List[typing.Any] = []
        for arg in arg_spec.args:
            for val in unpaired:
                val_type = type(val)
                if cls.type_matches_annotation(val_type, arg_spec.annotations[arg]):
                    p_args.append(val)
                    unpaired.remove(val)
                    break

        p_kwonlyargs: typing.Dict[str, typing.Any] = {}
        for arg in arg_spec.kwonlyargs:
            for val in unpaired:
                val_type = type(val)
                if cls.type_matches_annotation(val_type, arg_spec.annotations[arg]):
                    p_kwonlyargs[arg] = val
                    unpaired.remove(val)
                    break

        p_vargs: typing.List[typing.Any] = []
        if len(unpaired) > 0 and arg_spec.varargs is not None:
            p_vargs[arg_spec.varargs] = unpaired

        return func(*p_args, *p_vargs, **p_kwonlyargs)


nuco = Infix(lambda x, y: y if x is None else x)
"""Null coalescing operator
"""


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
    def from_match(
        cls,
        match: regex.Match,
        *exclude_keys: Types.C_GK,
        desc: str | Types.F_M_GK_2_DESC = lambda m, gk: str(gk)
    ) -> Types.C_ITO:
        if match is None:
            raise Errors.parameter_not_none('match')
        elif not isinstance(match, regex.Match):
            raise Errors.parameter_invalid_type('match', match, regex.Match)

        if 0 in exclude_keys:
            raise ValueError('group key 0 cannot be excluded')

        # Include all named keys, unless in exclude_keys or same group excluded by index
        gn_spans: typing.Dict[Types.C_GK, typing.List[typing.Tuple[int]]] = {
            k: match.spans(k)
            for k in match.re.groupindex.keys()
            if k not in exclude_keys and match.re.groupindex[k] not in exclude_keys
        }

        # Include all remaining int keys
        gn_spans |= {
            i: match.spans(i)
            for i in range(1, match.re.groups + 1)
            if i not in exclude_keys and i not in match.re.groupindex.values()
        }

        if isinstance(desc, str):
            desc_func = lambda match, group: desc
        elif Types.is_callable(desc, Types.F_M_GK_2_DESC):
            desc_func = desc
        else:
            raise Errors.parameter_invalid_type('desc', desc, Types.F_M_GK_2_DESC)

        path_stack: typing.List[Types.C_ITO] = []
        match_itos: typing.List[Types.C_ITO] = []
        gn_span_tups = [(gn, span) for gn, spans in gn_spans.items() for span in spans]
        for gn, span in sorted(gn_span_tups, key=lambda val: (val[1][0], -val[1][1])):
            ito = cls(match.string, *span, desc=desc_func(match, gn))
            while len(path_stack) > 0 and (ito.start < path_stack[-1].start or ito.stop > path_stack[-1].stop):
                path_stack.pop()
            if len(path_stack) == 0:
                match_itos.append(ito)
            else:
                path_stack[-1].children.add(ito)

            path_stack.append(ito)

        # Entire match serves as root
        rv = cls(match.string, *match.span(), desc=desc_func(match, 0))
        rv.children.add(*match_itos)
        return rv

    @classmethod
    def from_match_group(cls,
        match: regex.Match,
        group: Types.C_GK = 0,
        desc: str | Types.F_M_GK_2_DESC = lambda m, gk: str(gk)
    ) -> Types.C_ITO:
        if match is None:
            raise Errors.parameter_not_none('match')
        elif not isinstance(match, regex.Match):
            raise Errors.parameter_invalid_type('match', match, regex.Match)

        if group is None:
            raise Errors.parameter_not_none('group')

        if isinstance(desc, str):
            desc_func = lambda m, g: desc
        elif Types.is_callable(desc, Types.F_M_GK_2_DESC):
            desc_func = desc
        else:
            raise Errors.parameter_invalid_type('desc', desc, Types.F_M_GK_2_DESC)

        return cls(match.string, *match.span(group), desc=desc_func(match, group))

    @classmethod
    def from_re(
            cls,
            re: regex.Pattern,
            src: str | Types.C_ITO,
            *exclude_keys: Types.C_GK,
            desc: str | Types.F_M_GK_2_DESC = lambda m, gk: str(gk),
            limit: int | None = None,
    ) -> typing.Iterable[Types.C_ITO]:
        if not isinstance(re, regex.Pattern):
            raise Errors.parameter_invalid_type('re', re, regex.Pattern)

        if isinstance(src, str):
            s = src
            span = Span.from_indices(s)
        elif isinstance(src, Ito):
            s = src.string
            span = src.span
        else:
            raise Errors.parameter_invalid_type('src', src, str, Ito)

        for count, m in enumerate(re.finditer(s, *span), 1):
            yield cls.from_match(m, *exclude_keys, desc=desc)
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
            substrings: typing.Iterable[str],
            desc: str | None = None
    ) -> typing.Iterable[Types.C_ITO]:
        """Generate Itos from substrings

        Args:
            src: a str or Ito to use as the basis
            substrings: iterable strings in src that:
                1. are present in string
                2. are ordered left to right
                3. are non-overlapping

                To capture a repeated substring, it must be repeated in the substrings parameter, e.g.:

                    given:

                        string = 'ababce'

                    when substrings =

                        ('ab', 'ce') -> returns 2 Ito objects with spans (0,2) and (4,6)

                        ('ab', 'ab', 'ce') -> returns 3 Ito objects with spans (0,2), (2,4) and (4,6)
            desc: a descriptor for the generated Itos

        Yields:
            Itos; stream ordering will be left to right
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

    def __getstate__(self):
        return {
            '_string': self._string,
            '_span': self._span,
            'desc': self.desc,
            '_children': self._children,
        }

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._value_func = None
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
    def _json_decoder_stringless(cls, obj: typing.Dict) -> Types.C_ITO | typing.Dict:
        if (t := obj.get('__type__')) is not None and t == 'Ito':
            rv = cls('', desc=obj['desc'])
            rv._span = Span(*obj['span'])
            rv.children.add(*obj['children'])
            return rv
        else:
            return obj

    @classmethod
    def json_decode_stringless(cls, string: str, json_data: str) -> Types.C_ITO:
        rv = json.loads(json_data, object_hook=cls._json_decoder_stringless)
        rv._set_string(string)
        return rv

    @classmethod
    def json_decoder(cls, obj: typing.Dict) -> Types.C_ITO | typing.Dict:
        if (t := obj.get('__type__')) is not None:
            if t == 'typing.Tuple[str, Ito]':
                rv = obj['ito']
                rv._string = obj['string']
                return rv
            elif t == 'Ito':
                return cls._json_decoder_stringless(obj)
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
    
    def __iter__(self) -> typing.Iterable[Ito]:
        length = len(self)
        if length == 1:
            yield self
        elif length > 1:
            for i in range(*self.span):
                yield self.clone(i, i + 1, clone_children=False)

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
                                            
        return self.clone(*span, clone_children=False)

    _format_int_directives = ['span', 'start', 'stop']
    _format_str_directives = ['desc', 'string', 'substr', 'value']
    _pat_format_zero_whitespace = r'(?P<zws> )'

    """ Python 3.11 format spec mini language is:
    
    [[fill]align][sign][z][#][0][width][grouping_option][.precision][type]
    
    See https://docs.python.org/3/library/string.html?highlight=fill%20align%20sign%20width#format-specification-mini-language"""

    _pat_format_int = r'(?P<dir>' + '|'.join(_format_int_directives) + r')' \
                      r'(?:\:' \
                      r'(?:(?P<fill>.)?(?P<align>[\<\>\=\^]))?' \
                      r'(?P<sign>[\+\-])?' \
                      r'(?P<hash>#)?' \
                      r'(?P<zero>0)?' \
                      r'(?P<width>\d+)?' \
                      r'(?P<grouping_option>[_,])?' \
                      r'(?P<type>[bcdeEfFgGnosxX%])?' \
                      r')?'
    _pat_format_str = r'(?P<dir>' + '|'.join(_format_str_directives) + r')' \
                      r'(?:\!' \
                      r'(?P<lslice>\d+)?' \
                      r'(?P<conv>[ars])' \
                      r'(?P<rslice>\d+)?' \
                      r')?' \
                      r'(?:\:' \
                      r'(?P<abbr_pos>[\<\^\>])?' \
                      r'(?P<width>\d+)' \
                      r'(?P<abbr>.+)?' \
                      r')?'
    _pat_format = '|'.join([_pat_format_zero_whitespace, _pat_format_int, _pat_format_str])
    _pat_format = r'%(?:' + _pat_format + r')'
    _re_format = regex.compile(_pat_format, regex.DOTALL)

    def __format__(self, format_spec: str) -> str:
        if format_spec is None or format_spec == '':
            return str(self)

        idxs = [*find_escapes(format_spec, '%')]
        len_idxs = len(idxs)

        matches: typing.List[regex.Match] = []
        for i in range(0, len_idxs):
            start = idxs[i]
            if i == len_idxs - 1:
                m = self._re_format.match(format_spec, start)
            else:
                stop = idxs[i + 1]
                m = self._re_format.match(format_spec, start, stop)

            if m is not None:
                matches.append(m)

        rv = format_spec
        for m in matches[::-1]:
            if m.group('zws') is not None:
                rv = rv[:m.span()[0]] + rv[m.span()[1]:]
                continue

            directive = m.group('dir')
            if directive in self._format_int_directives:
                fstr = format_spec[m.span('dir')[1] + 1:m.span(0)[1]]
                if directive == 'span':
                    start = format(self.start, fstr)
                    stop = format(self.stop, fstr)
                    sub = f'({start}, {stop})'
                elif directive == 'start':
                    sub = format(self.start, fstr)
                else:  # 'stop'
                    sub = format(self.stop, fstr)

            elif directive in self._format_str_directives:
                if directive == 'string':
                    sub = self._string
                elif directive == 'desc':
                    sub = str(self.desc)
                elif directive == 'substr':
                    sub = self.__str__()
                else:  # 'value'
                    sub = str(self.value())

                if (conv := m.group('conv')) is not None:
                    if conv == 'a':
                        sub = ascii(sub)
                    elif conv == 'r':
                        sub = repr(sub)

                    if (lslice := m.group('lslice')) is not None:
                        lslice = int(lslice)
                    else:
                        lslice = 0
                    if (rslice := m.group('rslice')) is not None:
                        rslice = None if rslice == '0' else int(rslice)
                    sub = sub[slice(lslice, -rslice)]

                if (width := m.group('width')) is not None:
                    if (width := int(width)) < len(sub):
                        abbr = m.group('abbr') |nuco| ''
                        if (len_abbr := len(abbr)) >= width:
                            sub = abbr[len_abbr - width:]
                        else:
                            if (abbr_pos := m.group('abbr_pos')) == '<':
                                sub = abbr + sub[len_abbr - width:]
                            elif abbr_pos == '^':
                                post_len = (width - len_abbr) // 2
                                post = sub[-post_len:] if post_len > 0 else ''
                                pre = sub[:width - len(post) - len_abbr]  # will have len >= 1
                                sub = pre + abbr + post
                            else:  # will be empty or '>' (default)
                                sub = sub[:width - len_abbr] + abbr
            else:
                raise ValueError(f'unknown format directive \'%{directive}\'')

            rv = rv[:m.span()[0]] + sub + rv[m.span()[1]:]

        return rv

    # endregion

    # region combinatorics

    @classmethod
    def adopt(cls, itos: Types.C_IT_ITOS, desc: str | None = None) -> Types.C_ITO:
        """Creates a parent for a sequence of Itos

        Args:
            *itos: an arbitrarily ordered sequence of itos that have
                a) identical values for .string
                b) non-overlapping edges
            desc: a descriptor for the parent ito

        Returns:
            An Ito whose .span matches the min .start and max .stop of the
            input sequence, and to whose .children clones of the input sequence
            have been hierarchically added
        """
        _iter = iter(itos)
        try:
            ito = next(_iter)
        except StopIteration:
            raise ValueError(f'parameter \'{itos}\' is empty')
            
        string = ito._string
        start = ito.start
        stop = ito.stop
        children_lists: typing.List[ChildItos] = [ito.children]

        while True:
            try:
                ito = next(_iter)
            except StopIteration:
                break
                
            if string != ito.string:
                raise ValueError(f'parameter \'{itos}\' have differing values for .string')
            start = min(start, ito.start)
            stop = max(stop, ito.stop)
            children_lists.append(ito.children)
            
        rv = cls(string, start, stop, desc)
        
        for children in children_lists:
            rv.children.add_hierarchical(*(c.clone() for c in children))

        return rv

    @classmethod
    def join(cls, *itos: Types.C_ITO, desc: str | None = None) -> Types.C_ITO:
        """Combines Itos

        Args:
            *itos: one or more, arbitrarily ordered Itos that have
                identical values for .string; overlaps are fine
            desc: a descriptor for the resulting Ito

        Returns:
            An Ito whose .span matches the min .start and max .stop of the
            input sequence, and whose .children is empty (i.e., *itos are
            NOT added as children to the return value)
        """
        _iter = iter(itos)
        try:
            ito = next(_iter)
        except StopIteration:
            raise ValueError(f'parameter \'*itos\' lacks any items')

        string = ito._string
        start = ito.start
        stop = ito.stop

        while True:
            try:
                ito = next(_iter)
            except StopIteration:
                break
                
            if string != ito.string:
                raise ValueError(f'parameter \'itos\' have differing values for .string')
            start = min(start, ito.start)
            stop = max(stop, ito.stop)
            
        return cls(string, start, stop, desc)

    def strip_to_children(self) -> Types.C_ITO:
        """Creates a clone with span trimmed to match extent of children; returns self if .children is empty
        
        Returns:
            Self or clone with adjusted .span
        """
        if len(self.children) > 0:
            start = self.children[0].start
            stop = self.children[-1].stop
            if (start > self.start) or (stop < self.stop):
                return self.clone(start, stop)
        
        return self

    def invert_children(self) -> Types.C_ITO:
        """Creates a clone of the self having children in the gaps
        
        Returns:
            A clone whose children occupy the gaps of self.
            
            - If len(self) is zero: the returned clone will have no no children.
            
            - If self has no gaps: returned clone will have no children.

            - If self is empty: returned clone will have a single, contiguous child.
        """            
        rv = self.clone(clone_children=False)
        
        if len(self) == 0:
            return rv
            
        if len(self.children) == 0:
            rv.children.add(rv.clone())
            return rv
        
        left = self.children[0]
        if left.start > self.start:
            rv.children.add(rv.clone(stop=left.start, clone_children=False))
            
        for right in self.children[1:]:
            if left.stop < right.start:
                rv.children.add(rv.clone(left.stop, right.start, clone_children=False))
                
            left = right
            
        if left.stop < self.stop:
            rv.children.add(rv.clone(left.stop, self.stop, clone_children=False))
            
        return rv
    
    def split_iter(
            self,
            re: regex.Pattern,
            max_split: int = 0,
            keep_seps: bool = False,
            desc: str | typing.Callable | None = None
    ) -> typing.Iterable[Types.C_ITO]:
        count = 0
        i = self.start
        for m in self.regex_finditer(re):
            if max_split != 0 and max_split >= count:
                break
            span = Span(*m.span(0))
            stop = span.stop if keep_seps else span.start
            yield self.clone(i, stop, desc, False)
            i = span.stop

        if i < self.stop:
            yield self.clone(i, desc=desc, clone_children=False)
        elif i == self.stop:
            yield self.clone(i, i, desc, False)

    def split(
            self,
            re: regex.Pattern,
            max_split: int = 0,
            keep_seps: bool = False,
            desc: str | None = None
    ) -> typing.List[Types.C_ITO]:
        return [*self.split_iter(re, max_split, keep_seps, desc)]

    # endregion

    # region regex equivalence methods

    def regex_search(
            self,
            re: regex.Pattern,
            concurrent: bool | None = None,
            timeout: float | None = None
    ) -> regex.Match | None:
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
    ) -> regex.Match | None:
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
    ) -> regex.Match | None:
        return re.fullmatch(
            self.string,
            *self.span,
            concurrent=concurrent,
            timeout=timeout)

    def regex_split(self, re: regex.Pattern, maxsplit: int = 0) -> typing.List[Types.C_ITO]:
        return [*self.regex_splititer(re, maxsplit)]

    def regex_splititer(self, re: regex.Pattern, maxsplit: int = 0) -> typing.Iterable[Types.C_ITO]:
        yield from self.split_iter(re, max_split=maxsplit, keep_seps=False)

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
        
        return self if i == self.start else self.clone(i, clone_children=False)

    def str_rstrip(self, chars: str | None = None) -> Types.C_ITO:
        f_c_in = self.__f_c_in(chars)
        i = self.stop - 1
        while i >= 0 and f_c_in(i):
            i -= 1

        return self if i == self.stop - 1 else self.clone(stop=i + 1, clone_children=False)

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
                return self, self.clone(self.stop), self.clone(self.stop)
            else:
                j = i + self.start
                k = j + len(sep)
                return self.clone(stop=j, clone_children=False), self.clone(j, k, clone_children=False), self.clone(k, clone_children=False)

    def str_rpartition(self, sep) -> typing.Tuple[Types.C_ITO, Types.C_ITO, Types.C_ITO]:
        if sep is None:
            raise ValueError('must be str, not NoneType')
        elif sep == '':
            raise ValueError('empty separator')
        else:
            i = self.str_rfind(sep)
            if i < 0:
                return self.clone(self.stop), self.clone(self.stop), self
            else:
                j = i + self.start
                k = j + len(sep)
                return self.clone(stop=j, clone_children=False), self.clone(j, k, clone_children=False), self.clone(k, clone_children=False)

    def _nearest_non_ws_sub(self, start: int, reverse: bool = False) -> Types.C_ITO | None:
        start += self.start

        if reverse:
            stop = self.start -1
            step = -1
        else:
            stop = self.stop
            step = 1

        def from_idxs():
            if step == 1:
                return self.clone(non_ws_i, i, clone_children=False)
            else:
                return self.clone(i + 1, non_ws_i + 1, clone_children=False)

        non_ws_i: start
        in_ws = True
        for i in range(start, stop, step):
            c = self._string[i]
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

            i = len(self) - 1
            rv: typing.List[Types.C_ITO] = []
            while (sub := self._nearest_non_ws_sub(i, True)) is not None and maxsplit != 0:
                rv.append(sub)
                i = sub.start - 1
                maxsplit -= 1
            rv.reverse()

            if maxsplit == 0:
                head_stop = self.stop if len(rv) == 0 else rv[0].start
                head = self.clone(stop=head_stop, clone_children=False).str_rstrip()
                if len(head) > 0:
                    rv.insert(0, head)
            return rv

        elif not isinstance(sep, str):
            raise Errors.parameter_invalid_type('sep', sep, str, types.NoneType)

        elif sep == '':
            raise ValueError('empty separator')

        elif maxsplit == 0:
            return [self]

        else:
            rv: typing.List[Types.C_ITO] = []
            i = self.stop
            while (j := self._string.rfind(sep, self.start, i)) >= 0 and maxsplit != 0:
                rv.insert(0, self.clone(j + len(sep), i, clone_children=False))
                i = j
                maxsplit -= 1

            if len(rv) == 0:
                rv.append(self)
            else:
                rv.insert(0, self if i == self.stop else self.clone(stop=i, clone_children=False))

            return rv

    def str_split(self, sep: str = None, maxsplit: int = -1) -> typing.List[Types.C_ITO]:
        if sep is None:
            rv: typing.List[Types.C_ITO] = []
            if self._string == '':
                return rv

            i = 0
            while (sub := self._nearest_non_ws_sub(i)) is not None and maxsplit != 0:
                rv.append(sub)
                i = sub.stop
                maxsplit -= 1

            if maxsplit == 0:
                tail_start = self.start if len(rv) == 0 else rv[-1].stop
                tail = self.clone(tail_start, clone_children=False).str_lstrip()
                if len(tail) > 0:
                    rv.append(tail)
            return rv

        elif not isinstance(sep, str):
            raise Errors.parameter_invalid_type('sep', sep, str, types.NoneType)

        elif sep == '':
            raise ValueError('empty separator')

        elif maxsplit == 0:
            return [self]

        else:
            rv: typing.List[Types.C_ITO] = []
            i = self.start
            while (j := self._string.find(sep, i, self.stop)) >= 0 and maxsplit != 0:
                rv.append(self.clone(i, j, clone_children=False))
                i = j + len(sep)
                maxsplit -= 1

            if len(rv) == 0:
                rv.append(self)
            else:
                rv.append(self if i == self.start else self.clone(i, clone_children=False))

            return rv

    # Line separators taken from https://docs.python.org/3/library/stdtypes.html
    _splitlines_re = regex.compile(r'\r\n|\r|\n|\v|\x0b|\f|\x0c|\x1c|\x1d|\x1e|\x85|\u2028|\u2029', regex.DOTALL)

    def str_splitlines(self, keepends: bool = False, desc: str | None = None) -> typing.List[Types.C_ITO]:
        rv = [*self.split_iter(self._splitlines_re, 0, keepends, desc)]

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
            return self

    def str_removesuffix(self, suffix: str) -> Types.C_ITO:
        if self.str_endswith(suffix):
            return self.__class__(self, stop=-len(suffix), desc=self.desc)
        else:
            return self
        
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

    def find_all(
            self,
            path: pawpaw.Types.C_PATH,
            values: typing.Dict[str, typing.Any] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, Types.C_ITO], bool]] | None = None
    ) -> typing.Iterable[Types.C_ITO]:
        yield from pawpaw.query.find_all(path, self, values, predicates)

    def find(
            self,
            path: pawpaw.Types.C_PATH,
            values: typing.Dict[str, typing.Any] | None = None,
            predicates: typing.Dict[str, typing.Callable[[int, Types.C_ITO], bool]] | None = None
    ) -> Types.C_ITO | None:
        return pawpaw.query.find(path, self, values, predicates)

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
