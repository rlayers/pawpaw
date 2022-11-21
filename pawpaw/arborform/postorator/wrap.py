from abc import ABC, abstractmethod
import typing

from pawpaw import Ito, Types
from pawpaw.arborform.postorator import Postorator


class Wrap(Postorator):
    def __init__(self, f: Types.F_ITOS_2_BITOS):
        super().__init__()
        self.__f = f

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        yield from self.__f(itos)
