from __future__ import annotations
import enum
import types
from abc import ABC, abstractmethod
import collections.abc
import typing

import regex
from segments import Types, Errors, Ito, Span


class Itorator(ABC):
    def __init__(self):
        self.__itor_next: Types.F_ITO_2_ITOR | None = None
        self.__itor_children: Types.F_ITO_2_ITOR | None = None
        #self.post_process: typing.Callable[[Types.C_IT_ITOS], Types.C_IT_ITOS] = lambda itos: itos

    @property
    def itor_next(self) -> Types.F_ITO_2_ITOR:
        return self.__itor_next

    @itor_next.setter
    def itor_next(self, val: Itorator | Types.F_ITO_2_ITOR | None):
        if isinstance(val, Itorator):
            self.__itor_next = lambda ito: val
        elif val is None or isinstance(val, collections.abc.Callable):  # TODO : Better type checking on Callable
            self.__itor_next = val
        else:
            raise Errors.parameter_invalid_type('val', val, Itorator, Types.F_ITO_2_ITOR, types.NoneType)

    @property
    def itor_children(self) -> Types.F_ITO_2_ITOR:
        return self.__itor_children

    @itor_children.setter
    def itor_children(self, val: Itorator | Types.F_ITO_2_ITOR | None):
        if isinstance(val, Itorator):
            self.__itor_children = lambda ito: val
        elif val is None or isinstance(val, collections.abc.Callable):  # TODO : Better type checking on Callable
            self.__itor_children = val
        else:
            raise Errors.parameter_invalid_type('val', val, Itorator, Types.F_ITO_2_ITOR, types.NoneType)

    @abstractmethod
    def _iter(self, ito: Ito) -> Types.C_SQ_ITOS:
        pass

    def _do_children(self, ito: Ito) -> None:
        if self.__itor_children is not None:
            itor_c = self.__itor_children(ito)
            for c in itor_c._iter(ito):
                ito.children.add(c)
                for i in itor_c._do_next(c):
                    pass  # force iter walk

    def _do_next(self, ito: Ito) -> Types.C_IT_ITOS:
        if self.__itor_next is None:
            yield ito
        else:
            itor_n = self.__itor_next(ito)
            yield from itor_n._traverse(ito)

    def _traverse(self, ito: Ito) -> Types.C_IT_ITOS:
        # Process ._iter with parent in place:
        curs = self._iter(ito)
        
        # ...now remove from parent (if any)
        if (parent := ito.parent) is not None:
            parent.children.remove(ito)

        for cur in curs:
            if parent is not None:
                parent.children.add(cur)

            self._do_children(cur)

            yield from self._do_next(cur)

    def traverse(self, ito: Ito) -> Types.C_IT_ITOS:
        yield from self._traverse(ito.clone())


class Wrap(Itorator):
    def __init__(self, f: Types.F_ITO_2_SQ_ITOS):
        super().__init__()
        self.__f = f

    def _iter(self, ito: Ito) -> Types.C_SQ_ITOS:
        return self.__f(ito)


class Reflect(Itorator):
    def __init__(self):
        super().__init__()

    def _iter(self, ito: Ito) -> Types.C_SQ_ITOS:
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
        group: A key used to identify a group from the matches; the resulting group will be used as the boundary;
               defaults to 0 (the entire match)
        boundary_retention: A rule used to determine if boundaries are discarded, or else how they are kept
        desc: Value used to pass to the .clone method of a given Ito that is being split; note that because
              the returned Itos can be surrounded by 0, 1, or 2 boundaries, there is no clear desc_func that
              can be used to generate dynamic .desc values
        """
        super().__init__()
        self.re = re
        self.group = group
        self.boundary_retention = boundary_retention
        self.desc = desc
        
    def _iter(self, ito: Ito) -> Types.C_SQ_ITOS:
        rv: typing.List[Ito] = []
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
                
        if len(rv) == 0:
            rv.append(ito)

        return rv


class Extract(Itorator):
    Types.F_ITO_M_GK_2_B = typing.Callable[[Ito, regex.Match, str], bool]

    def __init__(self,
                 re: regex.Pattern,
                 limit: int | None = None,
                 desc_func: Types.F_ITO_M_GK_2_DESC = lambda ito, match, group: group,
                 group_filter: collections.abc.Container[str] | Types.F_ITO_M_GK_2_B | None = None):
        super().__init__()
        self.re = re
        self.limit = limit
        self.desc_func = desc_func
        self.group_filter = group_filter

    @property
    def group_filter(self) -> typing.Callable[[Ito, regex.Match, str], bool]:
        return self._group_filter
    
    @group_filter.setter
    def group_filter(self, group_filter: collections.abc.Container[str] | Types.F_ITO_M_GK_2_B | None) -> None:
        if group_filter is None:
            self._group_filter = lambda i, m_, g: True

        elif isinstance(group_filter, typing.Callable):  # TODO : Better type check
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

    def _iter(self, ito: Ito) -> Types.C_SQ_ITOS:
        rv: typing.List[Ito] = []
        for count, m in enumerate(ito.regex_finditer(self.re), 1):
            path_stack: typing.List[Ito] = []
            match_itos: typing.List[Ito] = []
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
