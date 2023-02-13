from __future__ import annotations

from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator


class Desc(Itorator):
    def __init__(self, desc: str | Types.F_ITO_2_DESC, tag: str | None = None):
        super().__init__(tag)
        if isinstance(desc, str):
            self._desc_func = lambda ito: desc
        elif type_magic.functoid_isinstance(desc, Types.F_ITO_2_DESC):
            self._desc_func = desc
        else:
            raise Errors.parameter_invalid_type('desc', desc, str | Types.F_ITO_2_DESC)

    def transform(self, ito: Ito) -> Types.C_SQ_ITOS:
        ito.desc = self._desc_func(ito)
        return ito,
