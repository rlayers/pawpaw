from __future__ import annotations

from pawpaw import Types, Errors
from pawpaw.arborform.itorator import Itorator


class Desc(Itorator):
    def __init__(self, desc: str | Types.F_ITO_2_DESC):
        super().__init__()
        if isinstance(desc, str):
            self._desc_func = lambda ito: desc
        elif Types.is_desc_func(desc):
            self._desc_func = desc
        else:
            raise Errors.parameter_invalid_type('desc', desc, str | Types.F_ITO_2_DESC)

    def _iter(self, ito: Types.C_ITO) -> Types.C_SQ_ITOS:
        ito.desc = self._desc_func(ito)
        return ito,
