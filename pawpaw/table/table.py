from abc import ABC, abstractmethod, abstractproperty
import dataclasses

import regex
import pawpaw


class Table(ABC):
    @property
    @abstractmethod
    def re(self) -> regex.Pattern:
        ...

    @abstractmethod
    def get_itor(self) -> pawpaw.arborform.Itorator:
        ...


@dataclasses.dataclass
class TableStyle:
    pre_caption_pat: str | None = None
    table_start_pat: str = ''
    header_row_end_pat: str | None = None
    row_sep_pat: str = ''
    table_end_pat: str | None = None
    post_caption_pat: str | None = None
    equi_distant_indent: bool = True


class StyledTable(Table):
    # finds equidistant indentation (zero or more spaces or tabs) chunks
    _pat_indent = r'[ \t]*'
    _re_equi_ident = regex.compile(rf'(?<=^|\n)(?P<chunk>(?P<indent>{_pat_indent})[^ \t][^\n]+?\n(?:(?P=indent)[^ \t][^\n]+?(?:\n|$))+)', regex.DOTALL)

    @classmethod
    def _build_re(cls, style: TableStyle) -> regex.Pattern:
        re = r'(?<=^|\n)'

        if style.equi_distant_indent:
            re = rf'(?P<indent>{cls._pat_indent})'
            pat_indent = r'(?P=indent)'
        else:
            pat_indent = r''

        re += r'(?<table>'

        if style.pre_caption_pat is not None:
            re += rf'(?:{style.pre_caption_pat}\n{pat_indent})?'

        re += rf'{style.table_start_pat}'

        if style.header_row_end_pat is not None:
            re += rf'(?:\n{pat_indent}(?<header_row>.+?)\n{pat_indent}{style.header_row_end_pat})?'
            
        if style.table_end_pat is None:
            re += rf'(?:\n{pat_indent}(?<row>.+?)\n{pat_indent}{style.row_sep_pat})+'
        else:
            re += rf'(?:\n{pat_indent}(?<row>.+?)\n{pat_indent}{style.row_sep_pat})*\n{pat_indent}(?<row>.+?)'
            re += rf'\n{pat_indent}{style.table_end_pat}'
            
        if style.post_caption_pat is not None:
            re += rf'\n{pat_indent}{style.post_caption_pat}(?=\n|$)'

        re += r')(?=$|\n)'

        return regex.compile(re, regex.DOTALL)

    def __init__(self, style: TableStyle, tag: str | None = None):
        self.style = style
        self._re = self._build_re(style)
        self.tag = tag

    @property
    def re(self) -> regex.Pattern:
        return self._re

    def get_itor(self) -> pawpaw.arborform.Itorator:
        itor_table = pawpaw.arborform.Extract(self._re, tag=self.tag, group_filter=lambda m, gk: gk in ('table', 'header_row', 'row'))
        if not self.style.equi_distant_indent:
            return itor_table

        itor_equi_ident = pawpaw.arborform.Extract(self._re_equi_ident, tag='equidistant indentation', group_filter=('chunk',))
        con = pawpaw.arborform.Connectors.Delegate(itor_table, 'chunk')
        itor_equi_ident.connections.append(con)
        return itor_equi_ident
