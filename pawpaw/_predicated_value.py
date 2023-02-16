from __future__ import annotations
import typing

from pawpaw import Errors, type_magic

P_A = typing.Callable[[typing.Any], bool]


class PredicatedValue:
    def __init__(self, predicate: P_A, value: typing.Any):
        if not type_magic.functoid_isinstance(predicate, P_A):
            raise Errors.parameter_invalid_type('predicate', predicate, P_A)
        self._predicate: P_A = predicate
        self._value: typing.Any = value

    @property
    def predicate(self) -> P_A:
        return self._predicate

    @property
    def value(self) -> typing.Any:
        return self._value
