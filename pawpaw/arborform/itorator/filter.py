from __future__ import annotations

from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator


class Filter(Itorator):
    def __init__(self, filter: Types.P_ITO, tag: str | None = None):
        super().__init__(tag)
        if not (filter is None or type_magic.functoid_isinstance(filter, Types.P_ITO)):
            raise Errors.parameter_invalid_type('filter', filter, Types.P_ITO)
        self._filter = filter

    def _transform(self, ito: Ito) -> Types.C_SQ_ITOS:
        if self._filter(ito):
            return ito,
        else:
            return ()
