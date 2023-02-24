from __future__ import annotations

from pawpaw import Ito, Types
from pawpaw.arborform.itorator import Itorator


class Reflect(Itorator):
    def __init__(self, tag: str | None = None):
        super().__init__(tag)

    def clone(self, tag: str | None = None) -> Reflect:
        return type(self())(self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        yield ito
