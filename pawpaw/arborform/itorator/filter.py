from __future__ import annotations

from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator


class Filter(Itorator):
    def __init__(self, filter_: Types.P_ITO, tag: str | None = None):
        super().__init__(tag)
        if not (filter_ is None or type_magic.functoid_isinstance(filter_, Types.P_ITO)):
            raise Errors.parameter_invalid_type('filter', filter_, Types.P_ITO)
        self._filter = filter_

    def clone(self, tag: str | None = None) -> Filter:
        return type(self())(self._filter, self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        if self._filter(ito):
            yield ito
