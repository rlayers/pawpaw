from __future__ import  annotations
import collections
import typing


class Errors:
    @classmethod
    def parameter_not_none(cls, name: str) -> ValueError:
        return ValueError(f'parameter \'{name}\' can not be None')

    @classmethod
    def parameter_invalid_type(cls, name: str, value: typing.Any, *allowed: typing.Type) -> TypeError:
        types = ' or '.join(t.__qualname__ for t in allowed)
        return TypeError(f'parameter \'{name}\' must be type {types}, not {type(value).__qualname__}')


class ErrorsEx:
    @classmethod
    def _type_checker(cls, val: typing.Any, t: typing.Type) -> bool:
        origin = typing.get_origin(t)
        if origin is typing.Union:
            return all(cls._type_checker(val, st) for st in typing.get_args(t))
        elif origin is collections.abc.Callable:
            return isinstance(val, collections.abc.Callable)  # TODO : Better check
        elif origin is None:
            return isinstance(val, origin)  # TODO : More sophisticated check against typing.get_args(t)
        else:
            return isinstance(val, t)