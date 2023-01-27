from __future__ import annotations
import typing

from pawpaw import Errors, type_magic

F_PREDICATE = typing.Callable[[typing.Any], bool]

class PredicatedValue:
    def __init__(self, predicate: F_PREDICATE, val: typing.Any):
        if not type_magic.functoid_isinstance(predicate, F_PREDICATE):
            raise Errors.parameter_invalid_type('predicate', predicate, F_PREDICATE)
        self._predicate: F_PREDICATE = predicate
        self._val: typing.Any = val

        @property
        def predicate(self) -> F_PREDICATE:
            return self._predicate

        @property
        def val(self) -> typing.Any:
            return self._val
