from __future__ import annotations
import inspect
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

    @classmethod
    def is_callable(cls, val: typing.Any, *params: typing.Type) -> bool:
        if not isinstance(val, typing.Callable):
            return False

        ips = inspect.signature(val).parameters
        if len(params) != len(ips):
            return False

        for ipv, p in zip(ips.values(), params):
            if ipv.annotation != inspect._empty and p != ipv.annotation:  # TODO : when p is singular type and annotation is Union
                return False

        return True