from __future__ import annotations
from abc import ABC, abstractmethod
import types
import typing
import enum

from pawpaw import Types, Errors, Ito, type_magic, PredicatedValue, Furcation
from pawpaw.arborform.postorator.postorator import Postorator


class Itorator(ABC):
    @classmethod
    def wrap(cls, src: Types.F_ITO_2_SQ_ITOS, tag: str | None = None):
        if type_magic.functoid_isinstance(src, Types.F_ITO_2_SQ_ITOS):
            return _WrappedItorator(src, tag)

        raise Errors.parameter_invalid_type('src', src, Types.F_ITO_2_SQ_ITOS)

    class ItorChildrenMode(enum.Enum):
        ADD = enum.auto()
        REPLACE = enum.auto()
        DEL = enum.auto()

    def __init__(self, tag: str | None = None):
        if tag is not None and not isinstance(tag, str):
            raise Errors.parameter_invalid_type('desc', tag, str)
        self.tag = tag
        self._itor_sub = Furcation[Ito, Itorator]()
        self._itor_children = Furcation[Ito, Itorator]()
        self._itor_children_mode = self.ItorChildrenMode.ADD
        self._itor_next = Furcation[Ito, Itorator]()
        self._postorator: Postorator | Types.F_ITOS_2_ITOS | None = None

    @property
    def itor_sub(self) -> Furcation[Ito, Itorator]():
        return self._itor_sub

    @itor_sub.setter
    def itor_sub(self, val: Itorator | PredicatedValue | tuple[typing.Callable[[Ito], bool], Itorator | None] | None) -> None:
        self._itor_sub.clear()
        if val is not None:
            self._itor_sub.append(val)

    @property
    def itor_children(self) -> Furcation[Ito, Itorator]():
        return self._itor_children

    @itor_children.setter
    def itor_children(self, val: Itorator | PredicatedValue | tuple[typing.Callable[[Ito], bool], Itorator | None] | None) -> None:
        self._itor_children.clear()
        if val is not None:
            self._itor_children.append(val)

    @property
    def itor_children_mode(self) -> ItorChildrenMode:
        return self._itor_children_mode

    @itor_children_mode.setter
    def itor_children_mode(self, mode: Itorator.ItorChildrenMode) -> None:
        if not isinstance(mode, self.ItorChildrenMode):
            raise Errors.parameter_invalid_type('mode', mode, self.ItorChildrenMode)

        if mode not in self.ItorChildrenMode:
            raise Errors.parameter_enum_not_in('mode', mode, self.ItorChildrenMode)

        self._itor_children_mode = mode

    @property
    def itor_next(self) -> Furcation[Ito, Itorator]():
        return self._itor_next

    @itor_next.setter
    def itor_next(self, val: Itorator | PredicatedValue | tuple[typing.Callable[[Ito], bool], Itorator | None] | None) -> None:
        self._itor_next.clear()
        if val is not None:
            self._itor_next.append(val)

    @property
    def postorator(self) -> Postorator | Types.F_ITOS_2_ITOS | None:
        return self._postorator

    @postorator.setter
    def postorator(self, val: Postorator | Types.F_ITOS_2_ITOS | None):
        if val is None or isinstance(val, Postorator):
            self._postorator = val
        else:
            raise Errors.parameter_invalid_type('val', val, Postorator, Types.F_ITOS_2_ITOS, types.NoneType)

    @abstractmethod
    def _transform(self, ito: Ito) -> Types.C_SQ_ITOS:
        pass

    def __do_sub(self, ito: Ito) -> Types.C_IT_ITOS:
        if (itor_s := self._itor_sub(ito)) is None:
            yield ito
        else:
            yield from itor_s._traverse(ito)

    def __do_children(self, ito: Ito):
        if (itor_c := self._itor_children(ito)) is not None:
            children = [*itor_c._traverse(ito)]

            if self._itor_children_mode == self.ItorChildrenMode.REPLACE:
                ito.children.clear()

            for c in children:
                if self._itor_children_mode in (self.ItorChildrenMode.ADD, self.ItorChildrenMode.REPLACE):
                    ito.children.add(c)
                else:  # self.ItorChildrenMode.DEL
                    ito.children.remove(c)

    def __do_next(self, ito: Ito) -> Types.C_IT_ITOS:
        if (itor_n := self._itor_next(ito)) is None:
            yield ito
        else:
            yield from itor_n._traverse(ito)

    def __do_prior_to_post(self, ito: Ito) -> Types.C_IT_ITOS:
        for i in self._transform(ito):
            for s in self.__do_sub(i):
                self.__do_children(s)
                yield from self.__do_next(s)

    def __do_post(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        if self._postorator is None:
            yield from itos
        else:
            yield from self._postorator(itos)

    def _traverse(self, ito: Ito) -> Types.C_IT_ITOS:
        yield from self.__do_post(self.__do_prior_to_post(ito))

    def __call__(self, ito: Ito) -> Types.C_IT_ITOS:
        if not isinstance(ito, Ito):
            raise Errors.parameter_invalid_type('ito', ito, Ito)
        yield from self._traverse(ito.clone())


class _WrappedItorator(Itorator):
    def __init__(self, f: Types.F_ITO_2_SQ_ITOS, tag: str | None = None):
        super().__init__(tag)
        self.__f = f

    def _transform(self, ito: Ito) -> Types.C_SQ_ITOS:
        return self.__f(ito)
