from __future__ import annotations
from abc import ABC, abstractmethod
import collections.abc
import enum
import itertools
import types
import typing

import regex
from pawpaw import Types, Errors, Ito, Span
from .postorator.postorator import Postorator


class Itorator(ABC):
    def __init__(self):
        self._itor_next: Itorator | Types.F_ITO_2_ITOR | None = None
        self._itor_children: Itorator | Types.F_ITO_2_ITOR | None = None
        self._postorator: Postorator | Types.F_ITOS_2_BITOS | None = None
        self._post_func: Types.F_ITOS_2_BITOS | None = None

    @property
    def itor_next(self) -> Types.F_ITO_2_ITOR:
        return self._itor_next

    @itor_next.setter
    def itor_next(self, val: Itorator | Types.F_ITO_2_ITOR | None):
        if val is self:
            raise ValueError('can\'t set .itor_next to self')
        elif isinstance(val, Itorator):
            self._itor_next = lambda ito: val
        elif val is None or Types.is_callable(val, Types.F_ITO_2_ITOR):
            self._itor_next = val
        else:
            raise Errors.parameter_invalid_type('val', val, Itorator, Types.F_ITO_2_ITOR, types.NoneType)

    @property
    def itor_children(self) -> Types.F_ITO_2_ITOR:
        return self._itor_children

    @itor_children.setter
    def itor_children(self, val: Itorator | Types.F_ITO_2_ITOR | None):
        if val is self:
            raise ValueError('can\'t set .itor_children to self')
        elif isinstance(val, Itorator):
            self._itor_children = lambda ito: val
        elif val is None or Types.is_callable(val, Types.F_ITO_2_ITOR):
            self._itor_children = val
        else:
            raise Errors.parameter_invalid_type('val', val, Itorator, Types.F_ITO_2_ITOR, types.NoneType)

    @property
    def postorator(self) -> Postorator | Types.F_ITOS_2_BITOS | None:
        return self._postorator

    @postorator.setter
    def postorator(self, val: Postorator | Types.F_ITOS_2_BITOS | None):
        if val is None or Types.is_callable(val, Types.F_ITOS_2_BITOS):
            self._postorator = self._post_func = val
        elif isinstance(val, Postorator):
            self._postorator = val
            self._post_func = val.traverse
        else:
            raise Errors.parameter_invalid_type('val', val, Postorator, Types.F_ITOS_2_BITOS, types.NoneType)

    @abstractmethod
    def _iter(self, ito: Types.C_ITO) -> Types.C_SQ_ITOS:
        pass

    def _do_children(self, ito: Types.C_ITO) -> None:
        if self._itor_children is not None:
            itor_c = self._itor_children(ito)
            if itor_c is not None:
                for c in itor_c._traverse(ito, True):
                    pass  # force iter walk

    def _do_next(self, ito: Types.C_ITO) -> Types.C_IT_ITOS:
        if self._itor_next is None:
            yield ito
        elif (itor_n := self._itor_next(ito)) is not None:
            yield from itor_n._traverse(ito)

    def _do_post(self, parent: Types.C_ITO, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        if self._post_func is None:
            yield from itos
        else:
            for bito in self._post_func(itos):
                if bito.tf:
                    if parent is not None and bito.ito.parent is not parent:
                        parent.children.add(bito.ito)
                    yield bito.ito
                elif (_parent := bito.ito.parent) is not None:
                    _parent.children.remove(bito.ito)

    def _traverse(self, ito: Types.C_ITO, as_children: bool = False) -> Types.C_IT_ITOS:
        # Process ._iter with parent in place
        curs = self._iter(ito)
        
        if as_children:
            parent = ito
        elif (parent := ito.parent) is not None:
            parent.children.remove(ito)  
  
        iters: typing.List[iter] = []
        for cur in curs:
            if parent is not None and cur.parent is not parent:
                parent.children.add(cur)

            self._do_children(cur)

            iters.append(self._do_next(cur))

        yield from self._do_post(parent, itertools.chain(*iters))

    def traverse(self, ito: Types.C_ITO) -> Types.C_IT_ITOS:
        yield from self._traverse(ito.clone())


class Wrap(Itorator):
    def __init__(self, f: Types.F_ITO_2_SQ_ITOS):
        super().__init__()
        self.__f = f

    def _iter(self, ito: Types.C_ITO) -> Types.C_SQ_ITOS:
        return self.__f(ito)


class Reflect(Itorator):
    def __init__(self):
        super().__init__()

    def _iter(self, ito: Types.C_ITO) -> Types.C_SQ_ITOS:
        return ito,


class Desc(Itorator):
    def __init__(self, desc: str | Types.F_ITO_2_DESC):
        super().__init__()
        if isinstance(desc, str):
            self._desc_func = lambda ito: desc
        elif Types.is_desc_func(desc):
            self._desc_func = desc
        else:
            raise Errors.parameter_invalid_type('desc', desc, str | Types.F_ITO_2_DESC)

    def _iter(self, ito: Types.C_ITO) -> Types.C_SQ_ITOS:
        ito.desc = self._desc_func(ito)
        return ito,


class Split(Itorator):
    @enum.unique
    class BoundaryRetention(enum.Enum):
        NONE = 0
        LEADING = 1
        TRAILING = 2

    def __init__(
        self,
        re: regex.Pattern,
        group: int | str = 0,
        boundary_retention: BoundaryRetention = BoundaryRetention.NONE,
        return_zero_split: bool = True,
        desc: str | None = None
    ):
        """Given P-O-O-S where P is prefix, - is boundary, O is/are middle part(s), and S is suffix, the
        behavior is as follows:

          * BoundaryRetention.NONE -> P O O S : boundaries are discarded (this is an 'ordinary' split operation)

          * BoundaryRetention.LEADING -> -O -O -S : boundaries kept as prefixes, leading P is discarded

          * BoundaryRetention.TRAILING -> P- O- O- : boundaries kept as suffixes, trailing S is discarded

        Zero-length boundaries are allowable, and any resulting empty Ito's are discarded

       Args:
        re: A regex pattern used to find matches
        group: A key used to identify a group from the matches; the resulting group will be used as the
          boundary; defaults to 0 (the entire match)
        boundary_retention: A rule used to determine if boundaries are discarded, or else how they are kept
        return_zero_split: Indicates how to handle the zero-split condition; when True and splits occur,
          returns a list containing a clone of the input Ito; when False and no splits occur, returns an
          empty list
        desc: Value used for the .desc of any returned Itos; note that a returned Ito can be surrounded by
          0, 1, or 2 boundaries, i.e., there is no clear mapping from a result to a boundary
        """
        super().__init__()
        self.re = re
        self.group = group
        self.boundary_retention = boundary_retention
        self.return_zero_split = return_zero_split
        self.desc = desc
        
    def _iter(self, ito: Types.C_ITO) -> Types.C_SQ_ITOS:
        rv: typing.List[Types.C_ITO] = []
        prior: Span | None = None
        for m in ito.regex_finditer(self.re):
            cur = Span(*m.span(self.group))
            if prior is None:
                if self.boundary_retention == self.BoundaryRetention.LEADING:
                    start = stop = 0
                else:
                    start = ito.start
                    if self.boundary_retention == self.BoundaryRetention.NONE:
                        stop = cur.start
                    else:  # TRAILING
                        stop = cur.stop
            else:
                if self.boundary_retention == self.BoundaryRetention.NONE:
                    start = prior.stop
                    stop = cur.start
                elif self.boundary_retention == self.BoundaryRetention.LEADING:
                    start = prior.start
                    stop = cur.start
                else:  # TRAILING
                    start = prior.stop
                    stop = cur.stop
            
            if start != stop:
                rv.append(ito.clone(start, stop, self.desc))
                          
            prior = cur

        if prior is not None and self.boundary_retention != self.BoundaryRetention.TRAILING:
            if self.boundary_retention == self.BoundaryRetention.NONE:
                start = prior.stop
            else:  # LEADING
                start = prior.start
            stop = ito.stop
            if start != stop:
                rv.append(ito.clone(start, stop, self.desc))
                
        if len(rv) == 0 and self.return_zero_split:
            rv.append(ito.clone(desc=self.desc))

        return rv


class Extract(Itorator):
    def __init__(self,
                 re: regex.Pattern,
                 limit: int | None = None,
                 desc_func: Types.F_ITO_M_GK_2_DESC = lambda ito, match, group: group,
                 group_filter: collections.abc.Container[str] | Types.F_ITO_M_GK_2_B | None = None):
        super().__init__()
        if not isinstance(re, regex.Pattern):
            raise Errors.parameter_invalid_type('re', re, regex.Pattern)
        self.re = re
        if limit is not None and not not isinstance(limit, int):
            raise Errors.parameter_invalid_type('limit', limit, int)
        self.limit = limit
        if not Types.is_callable(desc_func, Types.)
        if not isinstance(desc_func, Types.F_ITO_M_GK_2_DESC):
            raise Errors.parameter_invalid_type('desc_func', desc_func, Types.F_ITO_M_GK_2_DESC)
        self.desc_func = desc_func
        self.group_filter = group_filter

    @property
    def group_filter(self) -> typing.Callable[[Ito, regex.Match, str], bool]:
        return self._group_filter
    
    @group_filter.setter
    def group_filter(self, group_filter: collections.abc.Container[str] | Types.F_ITO_M_GK_2_B | None) -> None:
        if group_filter is None:
            self._group_filter = lambda i, m_, g: True

        elif Types.is_callable(group_filter, Types.F_ITO_M_GK_2_B):
            self._group_filter = group_filter

        elif isinstance(group_filter, collections.abc.Container):
            self._group_filter = lambda i, m_, g: g in group_filter

        else:
            raise Errors.parameter_invalid_type(
                'group_filter',
                group_filter,
                typing.Container[str],
                Types.F_ITO_M_GK_2_B,
                types.NoneType)

    def _iter(self, ito: Types.C_ITO) -> Types.C_SQ_ITOS:
        rv: typing.List[Types.C_ITO] = []
        for count, m in enumerate(ito.regex_finditer(self.re), 1):
            path_stack: typing.List[Types.C_ITO] = []
            match_itos: typing.List[Types.C_ITO] = []
            filtered_gns = (gn for gn in m.re.groupindex.keys() if self._group_filter(ito, m, gn))
            span_gns = ((span, gn) for gn in filtered_gns for span in m.spans(gn))
            for span, gn in sorted(span_gns, key=lambda val: (val[0][0], -val[0][1])):
                ito = ito.clone(*span, desc=self.desc_func(ito, m, gn), clone_children=False)
                while len(path_stack) > 0 and (ito.start < path_stack[-1].start or ito.stop > path_stack[-1].stop):
                    path_stack.pop()
                if len(path_stack) == 0:
                    match_itos.append(ito)
                else:
                    path_stack[-1].children.add(ito)

                path_stack.append(ito)

            rv.extend(match_itos)

            if self.limit is not None and self.limit == count:
                break

        return rv
