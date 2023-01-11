from abc import ABC, abstractmethod
import typing

from pawpaw import Ito, Types


class Postorator(ABC):
    @abstractmethod
    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        ...

    @classmethod
    def from_func(cls, f: Types.F_ITOS_2_BITOS):
        return _WrappedPostorator(f)


class _WrappedPostorator(Postorator):
    def __init__(self, f: Types.F_ITOS_2_BITOS):
        super().__init__()
        self.__f = f

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        yield from self.__f(itos)