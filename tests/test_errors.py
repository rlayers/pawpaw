import typing

from segments import Errors
from tests.util import _TestIto


class TestItorator(_TestIto):
    @classmethod
    def some_func(cls, a: str, b: int, c: bool) -> bool:
        return True

    def test_is_callable_for_def(self):
        self.assertTrue(Errors.is_callable(self.some_func, str, int, bool))
        self.assertFalse(Errors.is_callable(self.some_func, bool, int, str))

    def test_is_callable_for_lambda(self):
        my_lam: typing.Callable[[str, int, bool], bool] = lambda a, b, c: True
        self.assertTrue(Errors.is_callable(my_lam, str, int, bool))
        self.assertTrue(Errors.is_callable(my_lam, bool, int, str))
