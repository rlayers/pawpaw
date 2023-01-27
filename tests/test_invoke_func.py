from dataclasses import dataclass
import typing

import pawpaw
from tests.util import _TestIto


def arg_only_func(a: bool, b: int) -> typing.Dict[str, typing.Any]:
    return {'a': a, 'b': b}


def arg_kwonlyargs_func(a: bool, b: int = 1, c: float = 1.0, d: str = 'd param val') -> typing.Dict[str, typing.Any]:
    return {'a': a, 'b': b, 'c': c, 'd': d}


def big_func(a: bool, b: int = 1, *args, c: float = 1.0, d: str = 'd param val', **kwargs) -> typing.Dict[str, typing.Any]:
    return {'a': a, 'b': b, '*args': args, 'c': c, 'd': d, '**kwargs': kwargs}


class TestDescFunc(_TestIto):
    def test_arg_only_func(self):
        for vars in {'a': False, 'b': -1}, {'a': False, 'b': -1, 'c': 1.234}:
            with self.subTest(vars=vars):
                rv = pawpaw.type_magic.invoke_func(arg_only_func, *vars.values())
                for k, v in vars.items():
                    if k in ('a', 'b'):
                        self.assertEqual(v, rv[k])
                    else:
                        self.assertNotIn(k, rv.keys())

    def test_arg_kwonlyargs_func(self):
        for vars in {'a': True}, \
                    {'a': False, 'b': -1}, \
                    {'a': False, 'b': -1, 'c': 1.234}, \
                    {'a': False, 'b': -1, 'c': 1.234, 'd': 'd-value'}:
            with self.subTest(vars=vars):
                rv = pawpaw.type_magic.invoke_func(arg_kwonlyargs_func, *vars.values())
                for k, v in vars.items():
                    self.assertEqual(v, rv[k])

    def test_args(self):
        for vars in {'a': True}, {'a': False, 'b': -1}:
            with self.subTest(vars=vars):
                rv = pawpaw.type_magic.invoke_func(big_func, *vars.values())
                for k, v in vars.items():
                    self.assertEqual(v, rv[k])

    def test_args_kwargs(self):
        for vars in {'a': True, 'c': 1.234}, {'a': False, 'b': -1, 'c': 5.678}:
            with self.subTest(vars=vars):
                rv = pawpaw.type_magic.invoke_func(big_func, *vars.values())
                for k, v in vars.items():
                    self.assertEqual(v, rv[k])
