from pawpaw import Ito
from pawpaw.arborform import Reflect
from tests.util import _TestIto


class TestReflect(_TestIto):
    def test_iter(self):
        s = 'abc'
        root = Ito(s)
        self.add_chars_as_children(root, 'Child')

        reflect = Reflect()
        rv = reflect._transform(root)
        self.assertEqual(1, len(rv))
        self.assertIs(root, rv[0])
