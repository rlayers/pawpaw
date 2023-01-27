import dataclasses
import typing


from pawpaw import PredicatedValue
from tests.util import _TestIto, IntIto


def def_valid(i: int) -> bool:
    return i != 0


def def_invalid_ret_val(i: int) -> int:
    return i << 1


@dataclasses.dataclass
class _TestData:
    name: str
    expected_ctor_valid: bool
    functoid: typing.Callable


class TestPredicatedValue(_TestIto):
    def setUp(self) -> None:
        super().setUp()

        lam_valid_wo_type_hints = lambda i: i != 0
        lam_valid_w_type_hints: typing.Callable[[int], str] = lambda i: i != 0

        lam_invalid_rv_wo_type_hints = lambda i: i + 1
        lam_invalid_rv_w_type_hints: typing.Callable[[int], int] = lambda i: i + 1

        lam_invalid_param_count_wo_type_hints = lambda i, j: i != j
        lam_invalid_param_count_w_type_hints: typing.Callable[[int, int], str] = lambda i, j: i != j
        
        self.test_data = [
            _TestData('Valid lambda w/o type hints', True, lam_valid_wo_type_hints),
            _TestData('Valid lambda w/ type hints', True, lam_valid_w_type_hints),

            _TestData('Invalid lambda ret val w/o type hints', True, lam_invalid_rv_wo_type_hints),
            _TestData('Invalid lambda ret val w/ type hints', True, lam_invalid_rv_w_type_hints),  # ctor works because type lambda hints not yet inspectable by Python

            _TestData('Invalid lambda param count w/o type hints', False, lam_invalid_param_count_wo_type_hints),
            _TestData('Invalid lambda param count w/ type hints', False, lam_invalid_param_count_w_type_hints),

            _TestData('Valid def w/ type hints', True, def_valid),
            _TestData('Invalid def ret val w/ type hints', False, def_invalid_ret_val),
        ]

    def test_ctor(self):
        for ti in self.test_data:
            with self.subTest(type=ti.name):
                if ti.expected_ctor_valid:
                    self.assertIsNotNone(PredicatedValue(ti.functoid, object()))
                else:
                    with self.assertRaises(TypeError):
                        PredicatedValue(ti.functoid, object())
