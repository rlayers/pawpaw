from __future__ import annotations
from abc import ABC, abstractmethod
import dataclasses
import itertools
import types
import typing
import enum

from pawpaw import Types, Errors, Ito, type_magic
from pawpaw.arborform.postorator.postorator import Postorator


class Connector(ABC):
    pass

class Sub(Connector):
    pass

class Children(Connector):
    class Mode(enum.Enum):
        ADD = enum.auto()
        REPLACE = enum.auto()
        DELETE = enum.auto()

    def __init__(self, mode: Mode):
        self._mode = mode

    @property
    def mode(self) -> Mode:
        return self._mode

class Next(Connector):
    pass


@dataclasses.dataclass(frozen=True)
class Connection:
    connector: Connector
    itorator: ItoratorEx
    predicate: Types.P_ITO = lambda ito: True


class ItoratorEx(ABC):
    @classmethod
    def wrap(cls, src: Types.F_ITO_2_IT_ITOS, tag: str | None = None):
        if type_magic.functoid_isinstance(src, Types.F_ITO_2_IT_ITOS):
            return _WrappedItoratorEx(src, tag)

        raise Errors.parameter_invalid_type('src', src, Types.F_ITO_2_IT_ITOS)

    def __init__(self, tag: str | None = None):
        if tag is not None and not isinstance(tag, str):
            raise Errors.parameter_invalid_type('desc', tag, str)
        self._connections = list[Connection]()
        self.tag: str | None = tag
        self._postorator: Postorator | Types.F_ITOS_2_ITOS | None = None

    def clone(self, tag: str | None = None):
        return self(tag)

    @property
    def connections(self) -> List[Connection]:
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
    def _foo(self, ito: Ito, con_idx: int) -> Types.C_IT_ITOS:
        if con_idx >= len(self.connections):
            yield ito

        else:
            con = self._connections[con_idx]
            if con.predicate(ito):
                if isinstance(con.connector, Next):
                    yield from con.itorator._traverse(ito)

                elif isinstance(con.connector, Children):
                    children = [*con.itorator._traverse(ito)]

                    if con.connector.mode == Children.Mode.REPLACE:
                        ito.children.clear()

                    if con.connector.mode in (Children.Mode.ADD, Children.Mode.REPLACE):
                        ito.children.add(*children)
                    else:  # Children.Mode.DELETE
                        for c in children:
                            ito.children.remove(c)

                    yield from self._foo(ito, con_idx + 1)

                else:  # isinstance(con.connector, Sub)
                    for sub in con.itorator._traverse(ito):
                        yield from self._foo(sub, con_idx + 1)

            else:
                yield from self._foo(ito, con_idx + 1)

    def _post(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        if self._postorator is None:
            yield from itos
        else:
            yield from self._postorator(itos)                

    # soup to nuts
    def _traverse(self, ito: Ito) -> Types.C_IT_ITOS:
        for i in self._transform(ito):
            yield from self._post(self._foo(i, 0))

    def __call__(self, ito: Ito) -> Types.C_IT_ITOS:
        if not isinstance(ito, Ito):
            raise Errors.parameter_invalid_type('ito', ito, Ito)
        yield from self._traverse(ito.clone())


class _WrappedItoratorEx(ItoratorEx):
    def __init__(self, f: Types.F_ITO_2_IT_ITOS, tag: str | None = None):
        super().__init__(tag)
        self.__f = f

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        yield from self.__f(ito)


s = ' one two three '
root = Ito(s, 1, -1)
itor_wrd_split = ItoratorEx.wrap(lambda ito: ito.str_split())

itor_wrd_desc = ItoratorEx.wrap(lambda ito: [ito.clone(desc='word'),])
con = Connection(Sub(), itor_wrd_desc)
itor_wrd_split.connections.append(con)

itor_char_split = ItoratorEx.wrap(lambda ito: ito)
con = Connection(Children(Children.Mode.ADD), itor_char_split)
itor_wrd_split.connections.append(con)

itor_char_desc = ItoratorEx.wrap(lambda ito: [ito.clone(desc='char'),])
con = Connection(Sub(), itor_char_desc)
itor_char_split.connections.append(con)

itor_char_desc_vowel = ItoratorEx.wrap(lambda ito: [ito.clone(desc='char-vowel'),])
con = Connection(Sub(), itor_char_desc_vowel, lambda ito: str(ito) in 'aeiou')
itor_char_desc.connections.append(con)

from pawpaw.visualization import pepo
vtree = pepo.Tree()
for i in itor_wrd_split(root):
    print(vtree.dumps(i))
