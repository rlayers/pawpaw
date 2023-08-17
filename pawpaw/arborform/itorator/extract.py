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
                 desc_func: Types.F_ITO_M_GK_2_DESC = lambda ito, match, group_key: str(group_key),
                 group_filter: collections.abc.Container[str] | Types.P_ITO_M_GK | None = lambda ito, m, gk: isinstance(gk, str),
                 tag: str | None = None):
        super().__init__(re, group_filter, tag)

        if not isinstance(limit, (int, type(None))):
            raise Errors.parameter_invalid_type('limit', limit, int, types.NoneType)
        self.limit = limit

        if not type_magic.functoid_isinstance(desc_func, Types.F_ITO_M_GK_2_DESC):
            raise Errors.parameter_invalid_type('desc_func', desc_func, Types.F_ITO_M_GK_2_DESC)
        self.desc_func = desc_func

    def clone(self, tag: str | None = None) -> Extract:
        return type(self())(self._re, self.limit, self.desc_func, self._group_filter, self.tag if tag is None else tag)

    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        rv: typing.List[Ito] = []
        for count, m in enumerate(ito.regex_finditer(self._re), 1):
            path_stack: typing.List[Ito] = []
            match_itos: typing.List[Ito] = []
            filtered_gks = (gk for i, gk in enumerate(self._group_keys) if self.group_filter(ito, m, i) or self.group_filter(ito, m, gk))
            span_gks = ((span, gk) for gk in filtered_gks for span in m.spans(gk))
            for span, gk in sorted(span_gks, key=lambda val: (val[0][0], -val[0][1])):
                ito = ito.clone(*span, desc=self.desc_func(ito, m, gk), clone_children=False)
                while len(path_stack) > 0 and (ito.start < path_stack[-1].start or ito.stop > path_stack[-1].stop):
                    path_stack.pop()
                if len(path_stack) == 0:
                    match_itos.append(ito)
                else:
                    path_stack[-1].children.add(ito)

                path_stack.append(ito)

            rv.extend(match_itos)

            if self.limit is not None and self.limit == count:
                break

        return rv        
