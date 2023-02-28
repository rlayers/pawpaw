from __future__ import annotations
from abc import ABC, abstractmethod
import itertools
import types
import typing

from pawpaw import Types, Errors, Ito, type_magic
from pawpaw.arborform.postorator.postorator import Postorator


class Connector(ABC):
    def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
        self.itorator = itorator
        self.predicate = predicate


class ChildrenConnector(Connector, ABC):
    def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
        super().__init__(itorator, predicate)


class Connectors:
    class Next(Connector):
        def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
            super().__init__(itorator, predicate)

    class Sub(Connector):
        def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
            super().__init__(itorator, predicate)

    class Xxx(Connector):
        def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
            super().__init__(itorator, predicate)

    class Children:
        class Add(ChildrenConnector):
            def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
                super().__init__(itorator, predicate)

        class AddHierarchical(ChildrenConnector):
            def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
                super().__init__(itorator, predicate)

        class Replace(ChildrenConnector):
            def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
                super().__init__(itorator, predicate)

        class Delete(ChildrenConnector):
            def __init__(self, itorator: Itorator, predicate: Types.P_ITO = lambda ito: True):
                super().__init__(itorator, predicate)


class Itorator(ABC):
    @classmethod
    def __exhaust_iterator(cls, it: typing.Iterator):
        if not isinstance(it, typing.Iterator):
            raise Errors.parameter_invalid_type('it', it, typing.Iterator)
        
        while True:
            try:
                next(it)
            except StopIteration:
                break

    @classmethod
    def wrap(cls, src: Types.F_ITO_2_IT_ITOS, tag: str | None = None):
        if type_magic.functoid_isinstance(src, Types.F_ITO_2_IT_ITOS):
            return _WrappedItoratorEx(src, tag)

        raise Errors.parameter_invalid_type('src', src, Types.F_ITO_2_IT_ITOS)

    def __init__(self, tag: str | None = None):
        if tag is not None and not isinstance(tag, str):
            raise Errors.parameter_invalid_type('desc', tag, str)
        self._connections = list[Connector]()
        self.tag: str | None = tag
        self._postorator: Postorator | Types.F_ITOS_2_ITOS | None = None

    @abstractmethod
    def clone(self, tag: str | None = None) -> Itorator:
        ...

    @property
    def connections(self) -> list[Connector]:
        return self._connections

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
    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        pass

    # flow 
    def _flow(self, ito: Ito, con_idx: int) -> Types.C_IT_ITOS:
        if con_idx >= len(self.connections):
            yield ito

        else:
            con = self._connections[con_idx]
            if con.predicate(ito):
                if isinstance(con, Connectors.Next):
                    yield from con.itorator._traverse(ito)

                elif isinstance(con, ChildrenConnector):
                    children = [*con.itorator._traverse(ito)]

                    if isinstance(con, Connectors.Children.Replace):
                        ito.children.clear()

                    if isinstance(con, (Connectors.Children.Add, Connectors.Children.Replace)):
                        ito.children.add(*children)
                    elif isinstance(con, Connectors.Children.AddHierarchical):
                        ito.children.add_hierarchical(*children)
                    else:  # Connections.Children.Delete
                        for c in children:
                            ito.children.remove(c)

                    yield from self._flow(ito, con_idx + 1)

                elif isinstance(con, Connectors.Sub):
                    for sub in con.itorator._traverse(ito):
                        yield from self._flow(sub, con_idx + 1)

                elif isinstance(con, Connectors.Xxx):
                    self.__exhaust_iterator(con.itorator._traverse(ito))
                    yield from self._flow(ito, con_idx + 1)

                else:
                    raise TypeError('Invalid connector: {con}')

            else:
                yield from self._flow(ito, con_idx + 1)

    def _post(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        if self._postorator is None:
            yield from itos
        else:
            yield from self._postorator(itos)                

    # soup to nuts
    def _traverse(self, ito: Ito) -> Types.C_IT_ITOS:
        yield from self._post(itertools.chain.from_iterable(self._flow(i, 0) for i in self._transform(ito)))

    def __call__(self, ito: Ito) -> Types.C_IT_ITOS:
        if not isinstance(ito, Ito):
            raise Errors.parameter_invalid_type('ito', ito, Ito)
        yield from self._traverse(ito.clone())


class _WrappedItoratorEx(Itorator):
    def __init__(self, f: Types.F_ITO_2_IT_ITOS, tag: str | None = None):
        super().__init__(tag)
        self.__f = f

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        yield from self.__f(ito)

    def clone(self, tag: str | None = None) -> _WrappedItoratorEx:
        return type(self)(self.__f, self.tag if tag is None else tag)
