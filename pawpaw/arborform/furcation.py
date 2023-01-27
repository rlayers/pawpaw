from __future__ import annotations
import dataclasses
import typing
import types

from pawpaw import Ito, Types, Errors, type_magic, arborform

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

#########
# TESTS #
#########

def ValidPredicate(ito: Ito) -> bool:
    return True

def InvalidPredicate(ito: Ito) -> str:
    return 'abc'

it_root = arborform.Itorator.wrap(lambda ito: ito, tag='root')
it1 = arborform.Itorator.wrap(lambda ito: ito.str_ltrim(), tag='it1')
it2 = arborform.Itorator.wrap(lambda ito: ito.str_rtrim(), tag='it2')
it3 = arborform.Itorator.wrap(lambda ito: ito.str_split(), tag='it3')
        
ito_reg = Ito(' a b c ')
ito_ws = Ito('\t\t  ')
ito_empty = Ito('')

pv = PredicatedValue(lambda i: -1, 'Yes!')  # Ok: Invalid lambda rv, but no types available on lambdas so passes

pv = PredicatedValue(lambda i, j: True, 'Yes!')  # Invalid lambda param count

pv = PredicatedValue(InvalidPredicate, it1)  # Invalid predicate

pv = PredicatedValue(ValidPredicate, it1)  # OK

pv = PredicatedValue(lambda ito: False, it1)  # OK

P = typing.TypeVar('P')  # Input to predicate
R = typing.TypeVar('R')  # Return value type; should be "anything but None", but Python lacks this ability

class Furcation(list[PredicatedValue], typing.Generic[P, R]):
    def evaluate(self, ito: Ito) -> R | None:
        for pv in self:
            if pv.predicate(ito):
                return pv.val

        return None

    def append(self, item1: PredicatedValue | typing.Callable[[P], bool] | R, item2: R | None = None) -> None:
        p, r = typing.get_args(self.__orig_class__)

        if isinstance(item1, PredicatedValue):
            item = item1
        elif isinstance(item1, typing.Callable):
            if type_magic.functoid_isinstance(item1, typing.Callable[[p], bool]):
                if isinstance(item2, r) or item2 is None:
                    item = PredicatedValue(item1, item2)
                else:
                    raise Errors.parameter_invalid_type('item2', item2, *typing.get_args(r | None))
            else:
                raise Errors.parameter_invalid_type('item1', item1, PredicatedValue, typing.Callable[[p], bool], r)
        elif Types.type_matches_annotation(type(item1), r):
            item = PredicatedValue(lambda ito: True, item2)
        else:
            raise Errors.parameter_invalid_type('item1', item1, PredicatedValue, typing.Callable[[p], bool], r)

        super().append(item)

arc_list = Furcation[Ito, arborform.Itorator]()
