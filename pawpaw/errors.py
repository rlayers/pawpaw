from __future__ import annotations
import typing


class Errors:
    @classmethod
    def parameter_not_none(cls, name: str) -> ValueError:
        return ValueError(f'parameter \'{name}\' can not be None')

    @classmethod
    def parameter_neither_none_nor_empty(cls, name: str) -> ValueError:
        return ValueError(f'parameter \'{name}\' can be neither None nor emtpy')

    @classmethod
    def parameter_invalid_type(cls, name: str, value: typing.Any, *allowed: typing.Type) -> TypeError:
        types = ' or '.join(t.__qualname__ for t in allowed)
        return TypeError(f'parameter \'{name}\' must be type {types}, not {type(value).__qualname__}')
