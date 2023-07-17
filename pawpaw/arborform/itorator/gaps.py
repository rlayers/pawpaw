from __future__ import annotations

from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator


class Gaps(Itorator):
    def __init__(
            self,
            itorator: Itorator,
            desc: str | None = None,
            yield_non_gaps: bool = True,
            tag: str | None = None):
        super().__init__(tag)
        self.itorator = itorator
        self.desc = desc
        self.yield_non_gaps = yield_non_gaps

    def clone(self, tag: str | None = None) -> Gaps:
        return type(self())(self.itorator, self._desc_func, self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        start = ito.start
        for i in self.itorator(ito):
            if start < i.start:
                yield ito.clone(start, i.start, desc=self.desc)
            if self.yield_non_gaps:
                yield i
            start = i.stop

        if start == ito.start:
            yield ito.clone(desc=self.desc)
        elif i.stop < ito.stop:
            yield ito.clone(i.stop, ito.stop, self.desc)
