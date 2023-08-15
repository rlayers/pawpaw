from __future__ import annotations
import typing

from pawpaw import Ito, Types
from pawpaw.arborform.itorator import Itorator

class Nuco(Itorator):
    def __init__(self, *itorators: Itorator, tag: str | None = None):
        super().__init__(tag)
        self._itorators = list(itorators)

    def clone(self, tag: str | None = None) -> Nuco:
        return type(self())(self._itorators, self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        for itor in self._itorators:
            it = itor(ito)
            try:
                yield next(it)
                yield from it
                break
            except StopIteration:
                pass