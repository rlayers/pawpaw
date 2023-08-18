from __future__ import annotations

from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator


class Invert(Itorator):
    def __init__(
            self,
            itorator: Itorator,
            desc: str | None = None,
            tag: str | None = None):
        super().__init__(tag)
        self.itorator = itorator
        self.desc = desc

    def clone(self, tag: str | None = None) -> Invert:
        return type(self())(self.itorator, self.desc, self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        start = ito.start
        for i in self.itorator(ito):
            if start < i.start:
                yield ito.clone(start, i.start, desc=self.desc)
            start = i.stop

        if start == ito.start:
            yield ito.clone(desc=self.desc)
        elif i.stop < ito.stop:
            yield ito.clone(i.stop, ito.stop, self.desc)
