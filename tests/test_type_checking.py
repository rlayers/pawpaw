from dataclasses import dataclass
import typing

import pawpaw
from tests.util import _TestIto


class Foo:
    ...
    

class FooDerived(Foo):
    ...


T_RET = bool

T_A = str
T_B = int | None
T_C = Foo

F_EXACT = typing.Callable[[T_A, T_B, T_C], T_RET]
F_UNION_ELEMENT = typing.Callable[[T_A, int, T_C], T_RET]
F_SUBTYPE = typing.Callable[[T_A, T_B, FooDerived], T_RET]
F_TOO_FEW = typing.Callable[[T_A, T_B], T_RET]
F_TOO_MANY = typing.Callable[[T_A, T_B, T_C, T_A], T_RET]
F_WRONG_TYPES = typing.Callable[[T_C, T_B, T_A], T_RET]


def def_ub_w_typehints(a: T_A, b: T_B, c: T_C) -> T_RET:
    return True


def def_ub_wo_typehints(a, b, c):
    return True


@dataclass
class TestData:
    name: str
    type_hints: bool
    func: typing.Callable
        
        
class TestTypeChecking(_TestIto):
    @classmethod
    def def_cm_w_typehints(cls, a: T_A, b: T_B, c: T_C) -> T_RET:
        return True
    
    @classmethod
    def def_cm_wo_typehints(cls, a, b, c):
        return True
    
    def def_im_w_typehints(self, a: T_A, b: T_B, c: T_C) -> T_RET:
        return True
    
    def def_im_wo_typehints(self, a, b, c):
        return True

    def setUp(self) -> None:
        super().setUp()

        lam_w_typehints: typing.Callable[[T_A, T_B, T_C], T_RET] = lambda a, b, c: True
            
        lam_wo_typehints = lambda a, b, c: True
        
        self.test_data = [
            TestData('unbound def', True, def_ub_w_typehints),
            TestData('unbound def', False, def_ub_wo_typehints),
            TestData('class def', True, TestTypeChecking.def_cm_w_typehints),
            TestData('class def', False, TestTypeChecking.def_cm_wo_typehints),
            TestData('instance def', True, self.def_im_w_typehints),
            TestData('instance def', False, self.def_im_wo_typehints),
            TestData('lambda', True, lam_w_typehints),
            TestData('lambda', False, lam_wo_typehints),
        ]
            
    def test_is_callable_exact(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertTrue(pawpaw.Types.is_callable(ti.func, F_EXACT))

    def test_is_callable_union_element(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertTrue(pawpaw.Types.is_callable(ti.func, F_UNION_ELEMENT))

    def test_is_callable_subtype(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertTrue(pawpaw.Types.is_callable(ti.func, F_SUBTYPE))

    def test_is_callable_wrong_count(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertFalse(pawpaw.Types.is_callable(ti.func, F_TOO_FEW))
                self.assertFalse(pawpaw.Types.is_callable(ti.func, F_TOO_MANY))

    def test_is_callable_wrong_types(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                expected = not ti.type_hints or ti.name == 'lambda'  # type hints for lambdas don't show in annotations
                actual = pawpaw.Types.is_callable(ti.func, F_WRONG_TYPES)
                self.assertEqual(expected, actual)
