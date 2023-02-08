from __future__ import annotations
from abc import ABC, abstractmethod
import itertools
import types
import typing

from pawpaw import Types, Errors, Ito, type_magic, PredicatedValue, Furcation
from pawpaw.arborform.postorator.postorator import Postorator


class Itorator(ABC):
    # define Python user-defined exceptions
    class SelfChainingError(ValueError):
        """Raised when attempt is made to add self to the pipeline"""
        def __init__(self, type: str):
            self.message = f'can\t add self to {type} chain'

    def __init__(self, tag: str | None = None):
        if tag is not None and not isinstance(tag, str):
            raise Errors.parameter_invalid_type('desc', tag, str)
        self.tag = tag
        self._itor_children = Furcation[Ito, Itorator]()
        self._itor_sub = Furcation[Ito, Itorator]()
        self._itor_next = Furcation[Ito, Itorator]()
        self._postorator: Postorator | Types.F_ITOS_2_BITOS | None = None

    @property
    def itor_children(self) -> Furcation[Ito, Itorator]():
        return self._itor_children

    @itor_children.setter
    def itor_children(self, val: Itorator | PredicatedValue | tuple[typing.Callable[[Ito], bool], Itorator | None] | None) -> None:
        if (val is self) or (isinstance(val, PredicatedValue) and val.value is self) or (isinstance(val, tuple) and val[1] is self):
            raise Itorator.SelfChainingError('itor_children')

        self._itor_children.clear()
        if val is not None:
            self._itor_children.append(val)

    @property
    def itor_sub(self) -> Furcation[Ito, Itorator]():
        return self._itor_sub

    @itor_sub.setter
    def itor_sub(self, val: Itorator | PredicatedValue | tuple[typing.Callable[[Ito], bool], Itorator | None] | None) -> None:
        if (val is self) or (isinstance(val, PredicatedValue) and val.value is self) or (isinstance(val, tuple) and val[1] is self):
            raise Itorator.SelfChainingError('_itor_sub')

        self._itor_sub.clear()
        if val is not None:
            self._itor_sub.append(val)

    @property
    def itor_next(self) -> Furcation[Ito, Itorator]():
        return self._itor_next

    @itor_next.setter
    def itor_next(self, val: Itorator | PredicatedValue | tuple[typing.Callable[[Ito], bool], Itorator | None] | None) -> None:
        if (val is self) or (isinstance(val, PredicatedValue) and val.value is self) or (isinstance(val, tuple) and val[1] is self):
            raise Itorator.SelfChainingError('itor_next')

        self._itor_next.clear()
        if val is not None:
            self._itor_next.append(val)


    @property
    def postorator(self) -> Postorator | Types.F_ITOS_2_BITOS | None:
        return self._postorator

    @postorator.setter
    def postorator(self, val: Postorator | Types.F_ITOS_2_BITOS | None):
        if val is None or isinstance(val, Postorator):
            self._postorator = val
        else:
            raise Errors.parameter_invalid_type('val', val, Postorator, Types.F_ITOS_2_BITOS, types.NoneType)

    @abstractmethod
    def _iter(self, ito: Ito) -> Types.C_SQ_ITOS:
        pass

    def _do_children(self, ito: Ito) -> None:
        if (itor_c := self._itor_children.evaluate(ito)) is not None:
            for c in itor_c._traverse(ito, True):
                pass  # force iter walk

    def _do_sub(self, ito: Ito) -> Types.C_IT_ITOS:
        if (itor_s := self._itor_sub.evaluate(ito)) is None:
            yield ito
        else:
            yield from itor_s._traverse(ito)

    def _do_next(self, ito: Ito) -> Types.C_IT_ITOS:
        if (itor_n := self._itor_next.evaluate(ito)) is None:
            yield ito
        else:
            yield from itor_n._traverse(ito)

    def _do_post(self, parent: Ito, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        if self._postorator is None:
            yield from itos
        else:
            for bito in self._postorator.traverse(itos):
                if bito.tf:
                    if parent is not None and bito.ito.parent is not parent:
                        parent.children.add(bito.ito)
                    yield bito.ito
                elif (_parent := bito.ito.parent) is not None:
                    _parent.children.remove(bito.ito)

    def _traverse(self, ito: Ito, as_children: bool = False) -> Types.C_IT_ITOS:
        # Process ._iter & .itor_sub with parent in place
        curs = (s for i in self._iter(ito) for s in self._do_sub(i))
        
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

    def traverse(self, ito: Ito) -> Types.C_IT_ITOS:
        if not isinstance(ito, Ito):
            raise Errors.parameter_invalid_type('ito', ito, Ito)
        yield from self._traverse(ito.clone())

    @classmethod
    def wrap(cls, src: Types.F_ITO_2_SQ_ITOS, tag: str | None = None):
        if type_magic.functoid_isinstance(src, Types.F_ITO_2_SQ_ITOS):
            return _WrappedItorator(src, tag)

        raise Errors.parameter_invalid_type('src', src, Types.F_ITO_2_SQ_ITOS, Itorator)


class _WrappedItorator(Itorator):
    def __init__(self, f: Types.F_ITO_2_SQ_ITOS, tag: str | None = None):
        super().__init__(tag)
        self.__f = f

    def _iter(self, ito: Ito) -> Types.C_SQ_ITOS:
        return self.__f(ito)
