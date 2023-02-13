from abc import ABC, abstractmethod
import typing

from pawpaw import Types, type_magic, Errors


class Postorator(ABC):
    @classmethod
    def wrap(cls, func: Types.F_ITOS_2_ITOS, tag: str | None = None):
        if type_magic.functoid_isinstance(func, Types.F_ITOS_2_ITOS):
            return _WrappedPostorator(func, tag)

        raise Errors.parameter_invalid_type('func', func, Types.F_ITOS_2_ITOS)        

    def __init__(self, tag: str | None = None):
        if tag is not None and not isinstance(tag, str):
            raise Errors.parameter_invalid_type('desc', tag, str)
        self.tag = tag

    @abstractmethod
    def transform(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        ...

    def __call__(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        yield from self.transform(itos)   


class _WrappedPostorator(Postorator):
    def __init__(self, f: Types.F_ITOS_2_ITOS, tag: str | None = None):
        super().__init__(tag)
        self.__f = f

    def transform(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        yield from self.__f(itos)
