from __future__ import annotations
import types
from abc import ABC, abstractmethod
import collections.abc
import typing

import regex
from segments import Errors, Ito


F_ITO_2_ITOR = typing.Callable[[Ito], 'Itorator']

C_SQ_ITOS = typing.Sequence[Ito]
F_ITO_2_SQ_ITOS = typing.Callable[[Ito], C_SQ_ITOS]

C_IT_ITOS = typing.Iterable[Ito]
F_ITO_2_IT_ITOS = typing.Callable[[Ito], C_IT_ITOS]


class Itorator(ABC):
    def __init__(self):
        self.__itor_next: F_ITO_2_ITOR | None = None
        self.__itor_children: F_ITO_2_ITOR | None = None
        #self.post_process: typing.Callable[[C_IT_ITOS], C_IT_ITOS] = lambda itos: itos

    @property
    def itor_next(self) -> F_ITO_2_ITOR:
        return self.__itor_next

    @itor_next.setter
    def itor_next(self, val: Itorator | F_ITO_2_ITOR | None):
        if isinstance(val, Itorator):
            self.__itor_next = lambda ito: val
        elif val is None or isinstance(val, collections.abc.Callable):  # TODO : Better type checking on Callable
            self.__itor_next = val
        else:
            raise Errors.parameter_invalid_type('val', val, Itorator, F_ITO_2_ITOR, types.NoneType)

    @property
    def itor_children(self) -> F_ITO_2_ITOR:
        return self.__itor_children

    @itor_children.setter
    def itor_children(self, val: Itorator | F_ITO_2_ITOR | None):
        if isinstance(val, Itorator):
            self.__itor_children = lambda ito: val
        elif val is None or isinstance(val, collections.abc.Callable):  # TODO : Better type checking on Callable
            self.__itor_children = val
        else:
            raise Errors.parameter_invalid_type('val', val, Itorator, F_ITO_2_ITOR, types.NoneType)

    @abstractmethod
    def _iter(self, ito: Ito) -> C_SQ_ITOS:
        pass

    def _do_children(self, ito: Ito) -> None:
        if self.__itor_children is not None:
            itor_c = self.__itor_children(ito)
            for c in itor_c._iter(ito):
                ito.children.add(c)
                for i in itor_c._do_next(c):
                    pass  # force iter walk

    def _do_next(self, ito: Ito) -> C_IT_ITOS:
        if self.__itor_next is None:
            yield ito
        else:
            itor_n = self.__itor_next(ito)
            yield from itor_n._traverse(ito)

    def _traverse(self, ito: Ito) -> C_IT_ITOS:
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

    def traverse(self, ito: Ito) -> C_IT_ITOS:
        yield from self._traverse(ito.clone())


class Wrap(Itorator):
    def __init__(self, f: F_ITO_2_SQ_ITOS):
        super().__init__()
        self.__f = f

    def _iter(self, ito: Ito) -> C_SQ_ITOS:
        return self.__f(ito)


class Reflect(Itorator):
    def __init__(self):
        super().__init__()

    def _iter(self, ito: Ito) -> C_SQ_ITOS:
        return ito,


class Extract(Itorator):
    F_ITO_M_STR_2_B = typing.Callable[[Ito, regex.Match, str], bool]

    def __init__(self,
                 re: regex.Pattern,
                 limit: int | None = None,
                 desc_func: typing.Callable[[Ito, regex.Match, str], str] = lambda ito, match, group: group,
                 group_filter: collections.abc.Container[str] | F_ITO_M_STR_2_B | None = None):
        super().__init__()
        self.re = re
        self.limit = limit
        self.desc_func = desc_func
        self.group_filter = group_filter

    @property
    def group_filter(self) -> typing.Callable[[Ito, regex.Match, str], bool]:
        return self._group_filter
    
    @group_filter.setter
    def group_filter(self, group_filter: collections.abc.Container[str] | F_ITO_M_STR_2_B | None) -> None:
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
                self.F_ITO_M_STR_2_B,
                types.NoneType)

    def _iter(self, ito: Ito) -> C_SQ_ITOS:
        rv: typing.List[Ito] = []
        for count, m in enumerate(ito.regex_finditer(self.re), 1):
            path_stack: typing.List[Ito] = []
            match_itos: typing.List[Ito] = []
            filtered_gns = (gn for gn in m.re.groupindex.keys() if self._group_filter(ito, m, gn))
            span_gns = ((span, gn) for gn in filtered_gns for span in m.spans(gn))
            for span, gn in sorted(span_gns, key=lambda val: (val[0][0], -val[0][1])):
                ito = ito.clone(*span, self.desc_func(ito, m, gn))
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
