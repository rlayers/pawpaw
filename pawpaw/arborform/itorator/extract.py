from __future__ import annotations
import collections
import typing
import types

import regex
from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator

class Extract(Itorator):
    def __init__(self,
                 re: regex.Pattern,
                 limit: int | None = None,
                 desc_func: Types.F_ITO_M_GK_2_DESC = lambda ito, match, group_key: str(group_key),
                 group_filter: collections.abc.Container[str] | Types.P_ITO_M_GK | None = lambda ito, m, gk: isinstance(gk, str),
                 tag: str | None = None):
        super().__init__(tag)

        self._group_keys: list[Types.C_GK]
        self.re = re  # sets ._group_keys
        
        if limit is not None and not isinstance(limit, int):
            raise Errors.parameter_invalid_type('limit', limit, int)
        self.limit = limit

        self.desc_func = desc_func
        self.group_filter = group_filter  

    def clone(self, tag: str | None = None) -> Extract:
        return type(self())(self._re, self.limit, self.desc_func, self._group_filter, self.tag if tag is None else tag)

    @classmethod
    def _get_group_keys(cls, re: regex.Pattern) -> list[Types.C_GK]:
        rv = [i for i in range(0, re.groups + 1)]
        for n, i in re.groupindex.items():
            rv[i] = n
        return rv

    @property
    def re(self) -> regex.Pattern:
        return self._re

    @re.setter
    def re(self, re: regex.Pattern) -> None:
        if not isinstance(re, regex.Pattern):
            raise Errors.parameter_invalid_type('re', re, regex.Pattern)
        self._re = re
        self._group_keys = self._get_group_keys(re)

    @property
    def group_filter(self) -> typing.Callable[[Ito, regex.Match, Types.C_GK], bool]:
        return self._group_filter

    @group_filter.setter
    def group_filter(self, group_filter: collections.abc.Container[Types.C_GK] | Types.P_ITO_M_GK | None) -> None:
        if group_filter is None:
            self._group_filter = lambda i, m_, gk: True

        elif type_magic.functoid_isinstance(group_filter, Types.P_ITO_M_GK):
            self._group_filter = group_filter

        elif isinstance(group_filter, collections.abc.Container):
            self._group_filter = lambda i, m_, gk: gk in group_filter

        else:
            raise Errors.parameter_invalid_type(
                'group_filter',
                group_filter,
                typing.Container[Types.C_GK],
                Types.P_ITO_M_GK,
                types.NoneType)

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
