from __future__ import annotations
import inspect
import types
import typing
import enum


class Errors:
    @classmethod
    def parameter_not_none(cls, name: str) -> ValueError:
        return ValueError(f'parameter \'{name}\' can not be None')

    @classmethod
    def parameter_neither_none_nor_empty(cls, name: str) -> ValueError:
        return ValueError(f'parameter \'{name}\' can be neither None nor empty')

    @classmethod
    def parameter_enum_not_in(cls, name: str, value: typing.Any, enum_: enum.Enum) -> ValueError:
        return ValueError(f'parameter \'{name}\' is not a valid {enum_.__name__}')

    @classmethod
    def _get_type_strs(cls, *allowed) -> typing.Iterable[str]:
        for t in allowed:
            if hasattr(t, '__qualname__'):
                if t.__qualname__ == 'Callable':
                    yield str(t)
                else:
                    yield t.__qualname__
            elif hasattr(t, '__bound__'):
                yield from cls._get_type_strs(t.__bound__)
            elif typing.get_origin(t) is types.UnionType:
                args = typing.get_args(t)
                yield from cls._get_type_strs(*args)
            elif t is None:
                yield 'None'
            else:
                yield repr(t)

    @classmethod
    def _build_types_str(cls, *allowed: typing.Type) -> str:
        return ' or '.join(cls._get_type_strs(*allowed))

    @classmethod
    def parameter_invalid_type(cls, name: str, value: typing.Any, *allowed: typing.Type) -> TypeError:
        actual = str(inspect.signature(value)) if callable(value) else repr(value)
        return TypeError(f'parameter \'{name}\' must be type {cls._build_types_str(*allowed)}, not {actual}')

    @classmethod
    def parameter_iterable_contains_invalid_type(cls, name: str, value: typing.Any, *allowed: typing.Type) -> TypeError:
        actual = str(inspect.signature(value)) if callable(value) else repr(value)
        return TypeError(f'parameter \'{name}\' must contain elements of type {cls._build_types_str(*allowed)}, however, it contains an element of type {actual}: {value}')
