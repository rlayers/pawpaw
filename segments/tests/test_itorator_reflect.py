import typing

from segments import Ito
from segments.itorator import Reflect
from segments.tests.util import _TestIto


class TestItorator(_TestIto):
    def test_iter(self):
        s = 'abc'
        root = Ito(s)
        self.add_chars_as_children(root, 'Child')

        reflect = Reflect()
        rv = reflect._iter(root)
        self.assertEqual(1, len(rv))
        self.assertIs(root, rv[0])
