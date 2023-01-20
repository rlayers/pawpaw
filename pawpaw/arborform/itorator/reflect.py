from __future__ import annotations

from pawpaw import Types
from pawpaw.arborform.itorator import Itorator


class Reflect(Itorator):
    def __init__(self):
        super().__init__()

    def _iter(self, ito: pawpaw.Ito) -> Types.C_SQ_ITOS:
        return ito,
