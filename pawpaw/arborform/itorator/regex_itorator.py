from __future__ import annotations
from abc import abstractmethod
import collections
import typing
import types

import regex
from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator


class RegexItorator(Itorator):
    def __init__(self,
                 re: regex.Pattern,
                 group_filter: collections.abc.Container[str] | Types.P_ITO_M_GK | None = lambda ito, m, gk: isinstance(gk, str),
                 tag: str | None = None):
        super().__init__(tag)
        
        self._group_keys: list[Types.C_GK]
        self.re = re  # sets ._group_keys
        self.group_filter = group_filter

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

        elif type_magic.isinstance_ex(group_filter, collections.abc.Container[Types.C_GK]):
            self._group_filter = lambda i, m_, gk: gk in group_filter

        else:
            raise Errors.parameter_invalid_type(
                'group_filter',
                group_filter,
                typing.Container[Types.C_GK],
                Types.P_ITO_M_GK,
                types.NoneType)

    def clone(self, tag: str | None = None) -> RegexItorator:
        return type(self())(self._re, self.group_filter, self.tag)

    @abstractmethod
    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        pass
