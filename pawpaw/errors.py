from __future__ import annotations
import types
import typing


class Errors:
    @classmethod
    def parameter_not_none(cls, name: str) -> ValueError:
        return ValueError(f'parameter \'{name}\' can not be None')

    @classmethod
    def parameter_neither_none_nor_empty(cls, name: str) -> ValueError:
        return ValueError(f'parameter \'{name}\' can be neither None nor empty')

    @classmethod
    def _get_type_strs(cls, *allowed) -> typing.Iterable[str]:
        for t in allowed:
            if hasattr(t, '__qualname__'):
                yield t.__qualname__
            elif hasattr(t, '__bound__'):
                yield from cls._get_type_strs(t.__bound__)
            elif (origin := typing.get_origin(t)) is types.UnionType:
                args = typing.get_args(t)
                yield from cls._get_type_strs(*args)

    @classmethod
    def _build_types_str(cls, *allowed: typing.Type) -> str:
        return ' or '.join(cls._get_type_strs(*allowed))

    @classmethod
    def parameter_invalid_type(cls, name: str, value: typing.Any, *allowed: typing.Type) -> TypeError:
        return TypeError(f'parameter \'{name}\' must be type {cls._build_types_str(*allowed)}, not {type(value).__qualname__}')
