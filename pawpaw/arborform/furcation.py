from __future__ import annotations
import dataclasses
import typing
import types

from pawpaw import Ito, Types, Errors, arborform


T = typing.TypeVar('T', arborform.Itorator, arborform.Postorator)


@dataclasses.dataclass
class PredicatedValue(typing.Generic[T]):
    predicate: Types.F_ITO_2_B
    val: T | None

    def __post_init__(self):
        if not Types.is_callable(self.predicate, Types.F_ITO_2_B):
            raise Errors.parameter_invalid_type('predicate', self.predicate, Types.F_ITO_2_B)

        if not isinstance(self.val, (arborform.Itorator, arborform.Postorator)):
            raise Errors.parameter_invalid_type('val', self.val, arborform.Itorator, arborform.Postorator)


class Furcation(list[PredicatedValue[T]]):
    def evaluate(self, ito: Ito) -> T | None:
        for pv in self:
            if pv.predicate(ito):
                return pv.val

        return None

    def append(self, item1: PredicatedValue[T] | Types.F_ITO_2_B | T, item2: T = None) -> None:
        # Prefer PredicatedVal[T], but can't use subscripted generics for class and instance checks
        if isinstance(item1, PredicatedValue):
            item = item1
        elif Types.is_callable(item1, Types.F_ITO_2_B):
            if isinstance(item2, (arborform.Itorator, arborform.Postorator)) or item2 is None:
                item = PredicatedValue(item1, item2)
            else:
                raise Errors.parameter_invalid_type('item2', item2, arborform.Itorator, arborform.Postorator, None)
        # Prefer isinstance(item1, T), but this is not currently supported in Python
        elif isinstance(item1, (arborform.Itorator, arborform.Postorator)):
            item = PredicatedValue(lambda ito: True, item2)
        else:
            raise Errors.parameter_invalid_type('item1', item1, PredicatedValue[T], Types.F_ITO_2_B, arborform.Itorator, arborform.Postorator)

        super().append(item)


it_root = arborform.Itorator.wrap(lambda ito: ito, tag='root')
it1 = arborform.Itorator.wrap(lambda ito: ito.str_ltrim(), tag='it1')
it2 = arborform.Itorator.wrap(lambda ito: ito.str_rtrim(), tag='it2')
it3 = arborform.Itorator.wrap(lambda ito: ito.str_split(), tag='it3')

        
ito_reg = Ito(' a b c ')
ito_ws = Ito('\t\t  ')
ito_empty = Ito('')

#########
# TESTS #
#########

def ValidPredicate(ito: Ito) -> bool:
    return True

def InvalidPredicate(ito: Ito) -> str:
    return 'abc'

foo = PredicatedValue[arborform.Itorator](InvalidPredicate, it1)  # ValueError for predicate

foo = PredicatedValue[arborform.Itorator](ValidPredicate, 'abc')  # ValueError for 'val'

foo = PredicatedValue[arborform.Itorator](lambda ito: False, 'abc')  # ValueError for 'val'

foo = PredicatedValue[arborform.Itorator](ValidPredicate, it1)  # OK
foo = PredicatedValue[arborform.Itorator](lambda ito: False, it1)  # OK
