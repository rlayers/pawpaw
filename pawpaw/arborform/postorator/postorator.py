from abc import ABC, abstractmethod
import typing

from pawpaw import Ito, Types


class Postorator(ABC):
    @abstractmethod
    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        ...
