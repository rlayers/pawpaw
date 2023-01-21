from abc import ABC, abstractmethod
import typing

from pawpaw import Types, Errors


class Postorator(ABC):
    @abstractmethod
    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        ...

    @classmethod
    def wrap(cls, func: Types.F_ITOS_2_BITOS):
        return _WrappedPostorator(func)

    def __init__(self, tag: str | None = None):
        if tag is not None and not isinstance(tag, str):
            raise Errors.parameter_invalid_type('desc', tag, str)
        self.tag = tag


class _WrappedPostorator(Postorator):
    def __init__(self, f: Types.F_ITOS_2_BITOS):
        super().__init__()
        self.__f = f

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        yield from self.__f(itos)