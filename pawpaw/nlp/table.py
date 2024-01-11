from abc import ABC, abstractmethod, abstractproperty
import dataclasses

import regex
import pawpaw


@dataclasses.dataclass(frozen=True)
class TableStyle:
    start_pat: str = ''
    header_end_pat: str = ''
    row_end_pat: str = ''
    end_pat: str = ''


class Table(ABC):
    @abstractproperty
    def re(self) -> regex.Pattern:
        ...

    @abstractmethod
    def get_itor(self) -> pawpaw.arborform.Itorator:
        ...


class StyledTable(Table):
    @classmethod
    def _build_re(cls, style: TableStyle) -> regex.Pattern:
        return regex.compile('(?<=\n)(?<table>' + style.start_pat + '\n(?:.+?\n' + style.end_pat + ')+)', regex.DOTALL)

    def __init__(self, style: TableStyle, tag: str | None):
        self.style = style
        self._re = self._build_re(style)
        self.tag = tag

    @property
    def re(self) -> regex.Pattern:
        return self._re

    def get_itor(self) -> pawpaw.arborform.Itorator:
        return pawpaw.arborform.Extract(self._re, tag=self.tag)
