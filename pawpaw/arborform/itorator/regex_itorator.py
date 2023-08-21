from __future__ import annotations
from abc import abstractmethod
import collections
import typing
import types

import regex
from pawpaw import GroupKeys, Ito, Types, Errors, type_magic
from pawpaw.arborform.itorator import Itorator


class RegexItorator(Itorator):
    def __init__(self,
                 re: regex.Pattern,
                 group_filter: collections.abc.Container[Types.C_GK] | Types.P_M_GK = lambda m, gk: True,
                 tag: str | None = None):
        super().__init__(tag)
        
        self._group_keys: list[Types.C_GK]
        self.re = re  # sets ._group_keys
        self.group_filter = group_filter

    @property
    def re(self) -> regex.Pattern:
        return self._re

    @re.setter
    def re(self, re: regex.Pattern) -> None:
        if not isinstance(re, regex.Pattern):
            raise Errors.parameter_invalid_type('re', re, regex.Pattern)
        self._re = re
        self._group_keys = GroupKeys.preferred(re)

    @property
    def group_filter(self) -> collections.abc.Container[Types.C_GK] | Types.P_M_GK:
        return self._group_filter

    @group_filter.setter
    def group_filter(self, group_filter: collections.abc.Container[Types.C_GK] | Types.P_M_GK) -> None:
        if type_magic.isinstance_ex(group_filter, collections.abc.Container[Types.C_GK]):
            GroupKeys.validate(self._re, group_filter)
            self._group_filter = group_filter
        elif type_magic.functoid_isinstance(group_filter, Types.P_M_GK):
            self._group_filter = group_filter
        else:
            raise Errors.parameter_invalid_type('group_filter', group_filter, collections.abc.Container[Types.C_GK], Types.P_M_GK)

    def clone(self, tag: str | None = None) -> RegexItorator:
        return type(self())(self._re, self._group_filter, self.tag)

    @abstractmethod
    def _transform(self, ito: Ito) -> Types.C_IT_ITOS:
        pass
