from abc import ABC, abstractmethod, abstractproperty
import dataclasses

import regex
import pawpaw


@dataclasses.dataclass
class TableStyle:
    pre_caption_pat: str | None = None
    table_start_pat: str = ''
    header_row_end_pat: str | None = None
    row_sep_pat: str = ''
    table_end_pat: str | None = None
    post_caption_pat: str | None = None


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
        re = r'(?<=\n)(?<table>'

        if style.pre_caption_pat is not None:
            re += rf'(?:{style.pre_caption_pat}\n)?'

        re += rf'{style.table_start_pat}'

        if style.header_row_end_pat is not None:
            re += rf'(?:\n(?<header_row>.+?)\n{style.header_row_end_pat})?'
            
        if style.table_end_pat is None:
            re += rf'(?:\n(?<row>.+?)\n{style.row_sep_pat})+'
        else:
            re += rf'(?:\n(?<row>.+?)\n{style.row_sep_pat})*\n(?<row>.+?)'
            re += rf'\n{style.table_end_pat}'
            
        if style.post_caption_pat is not None:
            re += rf'\n{style.post_caption_pat}\n'

        re += r')'

        return regex.compile(re, regex.DOTALL)

    def __init__(self, style: TableStyle, tag: str | None = None):
        self.style = style
        self._re = self._build_re(style)
        self.tag = tag

    @property
    def re(self) -> regex.Pattern:
        return self._re

    def get_itor(self) -> pawpaw.arborform.Itorator:
        return pawpaw.arborform.Extract(self._re, tag=self.tag)
