import regex
from pawpaw import Ito
from pawpaw.arborform import ValueFunc
from tests.util import _TestIto


class TestValueFunc(_TestIto):
    def test_iter(self):
        s = '123'
        root = Ito(s)
        self.assertEqual(str(root), root.value())

        f = lambda i: int(str(i))
        itor = ValueFunc(f)
        rv = itor._iter(root)
        self.assertEqual(1, len(rv))

        rv = rv[0]
        self.assertIs(root, rv)
        self.assertEqual(f(rv), rv.value())
