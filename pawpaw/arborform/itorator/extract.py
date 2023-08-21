from __future__ import annotations
import collections
import types
import typing

import regex
from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import RegexItorator


class Extract(RegexItorator):
    def __init__(self,
                 re: regex.Pattern,
                 limit: int | None = None,
                 desc: str | Types.F_M_GK_2_DESC = lambda m, gk: str(gk),
                 group_filter: collections.abc.Container[Types.C_GK] | Types.P_M_GK = lambda m, gk: str(gk) != '0',
                 tag: str | None = None):
        super().__init__(re, group_filter, tag)

        if not isinstance(limit, (int, type(None))):
            raise Errors.parameter_invalid_type('limit', limit, int, types.NoneType)
        self.limit = limit

        if isinstance(desc, str):
            self._desc = lambda m, gk: desc
        elif type_magic.functoid_isinstance(desc, Types.F_M_GK_2_DESC):
            self.desc = desc
        else:
            raise Errors.parameter_invalid_type('desc', desc, str,  Types.F_M_GK_2_DESC)
    
    def clone(self, tag: str | None = None) -> Extract:
        return type(self())(self._re, self.limit, self.desc, self._group_filter, self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        return [*ito.from_re(self._re, ito, self.group_filter, self.desc, self.limit)]
