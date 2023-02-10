from abc import ABC, abstractmethod
import typing

from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.postorator import Postorator


class WindowedJoin(Postorator):
    F_SQ_ITOS_2_B = typing.Callable[[Types.C_SQ_ITOS], bool]
    
    def __init__(
            self,
            window_size: int,
            predicate: F_SQ_ITOS_2_B,
            ito_class: Ito = Ito,
            desc: str | None = None,
            tag: str | None = None
    ):
        super().__init__(tag)
        if not isinstance(window_size, int):
            raise Errors.parameter_invalid_type('window_size', window_size, int)
        if window_size < 2:
            raise ValueError(f'parameter \'window_size\' has value '
                             f'{window_size:,}, but must be greater than or equal to 2')
        self.window_size = window_size

        if not type_magic.functoid_isinstance(predicate, self.F_SQ_ITOS_2_B):
            raise Errors.parameter_invalid_type('predicate', predicate, self.F_SQ_ITOS_2_B)
        self.predicate = predicate

        if not issubclass(ito_class, Ito):
            raise ValueError('parameter \'ito_class\' ({ito_class}) is not an \'{Ito}\' or subclass.')
        self.ito_class = ito_class

        self.desc = desc

    def _traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        window: typing.List[Ito] = []
        for ito in itos:
            window.append(ito)
            if len(window) == self.window_size:
                if self.predicate(window):
                    joined = self.ito_class.join(*window, desc=self.desc)
                    yield from (Types.C_BITO(False, i) for i in window)
                    window.clear()
                    yield Types.C_BITO(True, joined)
                else:
                    yield Types.C_BITO(True, window.pop(0))

        yield from (Types.C_BITO(True, i) for i in window)
