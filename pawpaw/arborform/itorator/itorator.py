from __future__ import annotations
from abc import ABC, abstractmethod
import itertools
import types
import typing

from pawpaw import Types, Errors, Ito
from pawpaw.arborform.postorator.postorator import Postorator


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
    def _iter(self, ito: pawpaw.Ito) -> Types.C_SQ_ITOS:
        pass

    def _do_children(self, ito: pawpaw.Ito) -> None:
        if self._itor_children is not None:
            itor_c = self._itor_children(ito)
            if itor_c is not None:
                for c in itor_c._traverse(ito, True):
                    pass  # force iter walk

    def _do_next(self, ito: pawpaw.Ito) -> Types.C_IT_ITOS:
        if self._itor_next is None:
            yield ito
        elif (itor_n := self._itor_next(ito)) is not None:
            yield from itor_n._traverse(ito)

    def _do_post(self, parent: pawpaw.Ito, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
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

    def _traverse(self, ito: pawpaw.Ito, as_children: bool = False) -> Types.C_IT_ITOS:
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

    def traverse(self, ito: pawpaw.Ito) -> Types.C_IT_ITOS:
        if not isinstance(ito, Ito):
            raise Errors.parameter_invalid_type('ito', ito, pawpaw.Ito)
        yield from self._traverse(ito.clone())

    @classmethod
    def wrap(cls, src: Itorator | Types.F_ITO_2_SQ_ITOS):
        if isinstance(src, Itorator):
            return _WrappedItorator(src.traverse)
        
        if Types.is_callable(src, Types.F_ITO_2_SQ_ITOS):
            return _WrappedItorator(src)

        raise Errors.parameter_invalid_type('src', src, Types.F_ITO_2_SQ_ITOS, Itorator)


class _WrappedItorator(Itorator):
    def __init__(self, f: Types.F_ITO_2_SQ_ITOS):
        super().__init__()
        self.__f = f

    def _iter(self, ito: pawpaw.Ito) -> Types.C_SQ_ITOS:
        return self.__f(ito)
