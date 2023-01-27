from dataclasses import dataclass
import typing

import pawpaw
from tests.util import _TestIto


class Foo:
    ...
    

class FooDerived(Foo):
    ...


T_RET = bool

T_P1 = str
T_P2 = int | None
T_P3 = Foo
T_P4 = list[int]

F_EXACT = typing.Callable[[T_P1, T_P2, T_P3, T_P4], T_RET]
F_UNION_ELEMENT = typing.Callable[[T_P1, int, T_P3, T_P4], T_RET]
F_SUBTYPE = typing.Callable[[T_P1, T_P2, FooDerived, T_P4], T_RET]
F_NON_GENERIC = typing.Callable[[T_P1, T_P2, T_P3, list], T_RET]
F_INVALID_GENERIC = typing.Callable[[T_P1, T_P2, T_P3, list[str]], T_RET]
F_TOO_FEW = typing.Callable[[T_P1, T_P2, T_P3], T_RET]
F_TOO_MANY = typing.Callable[[T_P1, T_P2, T_P3, T_P4, bool], T_RET]
F_WRONG_RET = typing.Callable[[T_P1, T_P2, T_P3, T_P4], str]


def def_dir_w_type_hints(a: str, b: int | None, c: Foo, d: list[int]) -> bool:
    return True


def def_dir_wo_type_hints(a, b, c, d):
    return True


def def_indir_w_type_hints(a: T_P1, b: T_P2, c: T_P3, d: T_P4) -> T_RET:
    return True


def def_dir_subtype_w_type_hints(a: T_P1, b: T_P2, c: FooDerived, d: T_P4) -> T_RET:
    return True


@dataclass
class _TestData:
    name: str
    type_hints: bool
    subtype: bool
    functoid: typing.Callable
        
        
class TestTypeMagic(_TestIto):
    @classmethod
    def cls_m_w_type_hints(cls, a: T_P1, b: T_P2, c: T_P3, d: T_P4) -> T_RET:
        return True
    
    @classmethod
    def cls_m_wo_type_hints(cls, a, b, c, d):
        return True
    
    def inst_m_w_type_hints(self, a: T_P1, b: T_P2, c: T_P3, d: T_P4) -> T_RET:
        return self is not None
    
    def inst_m_wo_type_hints(self, a, b, c, d):
        return self is not None

    def setUp(self) -> None:
        super().setUp()

        lam_w_type_hints: typing.Callable[[T_P1, T_P2, T_P3, T_P4], T_RET] = lambda a, b, c, d: True

        lam_wo_type_hints = lambda a, b, c, d: True

        self.test_data = [
            _TestData('def direct', True, False, def_dir_w_type_hints),
            _TestData('def direct', False, False, def_dir_wo_type_hints),
            _TestData('def indirect', True, False, def_indir_w_type_hints),
            _TestData('def indirect subtype', True, True, def_dir_subtype_w_type_hints),
            _TestData('class method', True, False, TestTypeMagic.cls_m_w_type_hints),
            _TestData('class method', False, False, TestTypeMagic.cls_m_wo_type_hints),
            _TestData('instance method', True, False, self.inst_m_w_type_hints),
            _TestData('instance method', False, False, self.inst_m_wo_type_hints),
            _TestData('lambda', True, False, lam_w_type_hints),
            _TestData('lambda', False, False, lam_wo_type_hints),
        ]

    def test_is_callable_type_or_generic(self):
        for t in T_RET, T_P1, T_P2, T_P3, T_P4:
            with self.subTest(type=t):
                self.assertFalse(pawpaw.type_magic.is_callable_type_or_generic(t))

        for t in F_EXACT, F_UNION_ELEMENT, F_SUBTYPE, F_NON_GENERIC, F_INVALID_GENERIC, F_TOO_FEW, F_TOO_MANY, F_WRONG_RET:
            with self.subTest(type=t):
                self.assertTrue(pawpaw.type_magic.is_callable_type_or_generic(t))
    
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertFalse(pawpaw.type_magic.is_callable_type_or_generic(ti.functoid))
            
    def test_is_functoid(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertTrue(pawpaw.type_magic.is_functoid(ti.functoid))

    def test_is_def(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertEqual(ti.name.startswith('def'), pawpaw.type_magic.is_def(ti.functoid))

    def test_is_lambda(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertEqual(ti.name.startswith('lambda'), pawpaw.type_magic.is_lambda(ti.functoid))

    def test_is_callable_exact(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints):
                self.assertTrue(pawpaw.type_magic.functoid_isinstance(ti.functoid, F_EXACT))

    def test_is_callable_union_element(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints, subtype=ti.subtype):
                self.assertTrue(pawpaw.type_magic.functoid_isinstance(ti.functoid, F_UNION_ELEMENT))

    def test_is_callable_subtype(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints, subtype=ti.subtype):
                expected = not ti.type_hints or ti.name.startswith('lambda') or ti.subtype
                self.assertEqual(expected, pawpaw.type_magic.functoid_isinstance(ti.functoid, F_SUBTYPE))

    def test_is_callable_non_generic(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints, subtype=ti.subtype):
                self.assertTrue(pawpaw.type_magic.functoid_isinstance(ti.functoid, F_NON_GENERIC))

    def test_is_callable_invalid_generic(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints, subtype=ti.subtype):
                # Only compares origin (list to list), so everything will pass
                self.assertTrue(pawpaw.type_magic.functoid_isinstance(ti.functoid, F_INVALID_GENERIC))

    def test_is_callable_wrong_count(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints, subtype=ti.subtype):
                self.assertFalse(pawpaw.type_magic.functoid_isinstance(ti.functoid, F_TOO_FEW))
                self.assertFalse(pawpaw.type_magic.functoid_isinstance(ti.functoid, F_TOO_MANY))

    def test_is_callable_wrong_ret(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name, type_hints=ti.type_hints, subtype=ti.subtype):
                expected = not ti.type_hints or ti.name.startswith('lambda')  # type hints for lambdas don't show in annotations
                actual = pawpaw.type_magic.functoid_isinstance(ti.functoid, F_WRONG_RET)
                self.assertEqual(expected, actual)

        F_INT_2_NONE = typing.Callable[[int], None]

        def no_ret_val_w_type_hints(i: int) -> None:
            return

        with self.subTest(type=no_ret_val_w_type_hints.__name__, type_hints=True, subtype=False):
            actual = pawpaw.type_magic.functoid_isinstance(no_ret_val_w_type_hints, F_INT_2_NONE)
            self.assertTrue(actual)

        def no_ret_val_wo_type_hints(i):
            return

        with self.subTest(type=no_ret_val_wo_type_hints.__name__, type_hints=True, subtype=False):
            actual = pawpaw.type_magic.functoid_isinstance(no_ret_val_w_type_hints, F_INT_2_NONE)
            self.assertTrue(actual)



