from __future__ import annotations

from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator


class ValueFunc(Itorator):
    def __init__(self, f: Types.F_ITO_2_VAL | None, tag: str | None = None):
        super().__init__(tag)
        if not (f is None or type_magic.functoid_isinstance(f, Types.F_ITO_2_VAL)):
            raise Errors.parameter_invalid_type('f', f, Types.F_ITO_2_VAL, None)
        self.f = f

    def clone(self, tag: str | None = None) -> ValueFunc:
        return type(self())(self.f, self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        ito.value_func = self.f
        yield ito
