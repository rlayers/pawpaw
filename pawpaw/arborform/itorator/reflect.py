from __future__ import annotations

from pawpaw import Ito, Types
from pawpaw.arborform.itorator import Itorator


class Reflect(Itorator):
    def __init__(self, tag: str | None = None):
        super().__init__(tag)

    def transform(self, ito: Ito) -> Types.C_SQ_ITOS:
        return ito,
