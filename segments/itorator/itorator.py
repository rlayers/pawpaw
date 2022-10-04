from __future__ import annotations
from abc import ABC, abstractmethod
import collections
import enum
import typing
import enum
import typing

import regex
from segments import Errors, Span, Ito, ChildItos

C_ITOR_FUNC = typing.Callable[[Ito], 'Itorator']

class Itorator(ABC):
    def __init__(self):
        self.__itor_next: Itorator | None = None
        self.__itor_children: Itorator | None = None
        #self.post_process: typing.Callable[[typing.Iterable[Ito]], typing.Iterable[Ito]] = lambda itos: itos

    @property
    def itor_next(self) -> Itorator:
        return self.__itor_next

    @itor_next.setter
    def itor_next(self, itor: Itorator | C_ITOR_FUNC | None):
        if isinstance(itor, Itorator | None):
            self.__itor_next = itor
        elif isinstance(itor, collections.abc.Callable):
            self.__itor_next = Wrap(itor)
        else:
            raise Errors.parameter_invalid_type('itor', itor, Itorator, C_ITOR_FUNC, None)

    @property
    def itor_children(self) -> Itorator:
        return self.__itor_children

    @itor_children.setter
    def itor_children(self, itor: Itorator | C_ITOR_FUNC | None):
        if isinstance(itor, Itorator | None):
            self.__itor_children = itor
        elif isinstance(itor, collections.abc.Callable):
            self.__itor_children = Wrap(itor)
        else:
            raise Errors.parameter_invalid_type('itor', itor, Itorator, C_ITOR_FUNC, None)

    @abstractmethod
    def _iter(self, ito: Ito) -> typing.Iterable[Ito]:
        pass

    def _do_children(self, ito: Ito) -> None:
        if self.__itor_children is not None:
            ito.children.add(*self.__itor_children.traverse(ito))

    def _do_next(self, ito: Ito) -> typing.Iterable[Ito]:
        if self.__itor_next is None:
            yield ito
            return

        yield from self.__itor_next.traverse(ito)

    def traverse(self, ito: Ito) -> typing.Iterable[Ito]:
        for i in self._iter(ito.clone()):
            self._do_children(i)
            yield from self._do_next(i)


class Wrap(Itorator):
    def __init__(self, f: C_ITOR_FUNC):
        super().__init__()
        self.__f = f

    def _iter(self, ito: Ito) -> typing.Iterable[Ito]:
        yield from self.__f(ito)


class Reflect(Itorator):
    def __init__(self):
        super().__init__()

    def _iter(self, ito: Ito) -> typing.Iterable[Ito]:
        yield ito


class Extract(Itorator):
    def __init__(self,
                re: regex.Pattern,
                limit: int | None = None,
                descriptor_func: typing.Callable[[Ito, regex.Match, str], str] = lambda ito, match, group: group,
                group_filter: typing.abc.Container[str] | typing.Callable[[Ito, regex.Match, str], bool] | None = None):
        super().__init__()
        self.re = re
        self.limit = limit
        self.descriptor_func = descriptor_func
        self.group_filter = group_filter
        self._gf()  # Invoke to perform error check

    def _gf(self):
        if self.group_filter is None:
            return lambda i, m_, g: True

        if isinstance(self.group_filter, typing.Callable):  # TODO : Better type check
            return self.group_filter

        if isinstance(self.group_filter, collections.abc.Container):
            return lambda i, m_, g: g in self.group_filter

        raise Errors.parameter_invalid_type('group_filter', self.group_filter, typing.Container[str], typing.Callable[[Ito, regex.Match, str], bool], None)

    def _iter(self, ito: Ito) -> typing.Iterable[Ito]:
        for count, m in enumerate(ito.regex_finditer(self.re), 1):
            path_stack: typing.List[Ito] = []
            rv: typing.List[Ito] = []
            filtered_gns = (gn for gn in m.re.groupindex.keys() if self._gf()(ito, m, gn))
            span_gns = ((span, gn) for gn in filtered_gns for span in m.spans(gn))
            for span, gn in sorted(span_gns, key=lambda val: (val[0][0], -val[0][1])):
                ito = ito.clone(*span, self.descriptor_func(ito, m, gn))
                while len(path_stack) > 0 and (ito.start < path_stack[-1].start or ito.stop > path_stack[-1].stop):
                    path_stack.pop()
                if len(path_stack) == 0:
                    rv.append(ito)
                else:
                    path_stack[-1].children.add(ito)

                path_stack.append(ito)

            yield from rv

            if self.limit is not None and self.limit == count:
                return


