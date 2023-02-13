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
                 desc_func: Types.F_ITO_M_GK_2_DESC = lambda ito, match, group: group,
                 group_filter: collections.abc.Container[str] | Types.F_ITO_M_GK_2_B | None = None,
                 tag: str | None = None):
        super().__init__(tag)
        if not isinstance(re, regex.Pattern):
            raise Errors.parameter_invalid_type('re', re, regex.Pattern)
        self.re = re
        if limit is not None and not isinstance(limit, int):
            raise Errors.parameter_invalid_type('limit', limit, int)
        self.limit = limit
        if not type_magic.functoid_isinstance(desc_func, Types.F_ITO_M_GK_2_DESC):
            raise Errors.parameter_invalid_type('desc_func', desc_func, Types.F_ITO_M_GK_2_DESC)
        self.desc_func = desc_func
        self.group_filter = group_filter

    @property
    def group_filter(self) -> typing.Callable[[Ito, regex.Match, str], bool]:
        return self._group_filter

    @group_filter.setter
    def group_filter(self, group_filter: collections.abc.Container[str] | Types.F_ITO_M_GK_2_B | None) -> None:
        if group_filter is None:
            self._group_filter = lambda i, m_, g: True

        elif type_magic.functoid_isinstance(group_filter, Types.F_ITO_M_GK_2_B):
            self._group_filter = group_filter

        elif isinstance(group_filter, collections.abc.Container):
            self._group_filter = lambda i, m_, g: g in group_filter

        else:
            raise Errors.parameter_invalid_type(
                'group_filter',
                group_filter,
                typing.Container[str],
                Types.F_ITO_M_GK_2_B,
                types.NoneType)

    def transform(self, ito: Ito) -> Types.C_SQ_ITOS:
        rv: typing.List[Ito] = []
        for count, m in enumerate(ito.regex_finditer(self.re), 1):
            path_stack: typing.List[Ito] = []
            match_itos: typing.List[Ito] = []
            filtered_gns = (gn for gn in m.re.groupindex.keys() if self._group_filter(ito, m, gn))
            span_gns = ((span, gn) for gn in filtered_gns for span in m.spans(gn))
            for span, gn in sorted(span_gns, key=lambda val: (val[0][0], -val[0][1])):
                ito = ito.clone(*span, desc=self.desc_func(ito, m, gn), clone_children=False)
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
