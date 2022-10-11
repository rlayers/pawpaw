from unittest import TestCase

import regex
from segments import Ito
from segments.tests.util import _TestIto


class TestItoQuery(_TestIto):
    def setUp(self) -> None:
        self.src = 'nine 9 ten 10 eleven 11 twelve 12 thirteen 13'
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)(?: |$))+')
        self.root = Ito(self.src, desc='root')
        self.root.children.add(*Ito.from_re(re, self.src))

    # region axis

    def test_axis_self(self):
        i = self.root.find('.')
        self.assertIs(self.root, i)

    def test_axis_children(self):
        children = [*self.root.find_all('*')]
        self.assertListEqual([*self.root.children], children)

    def test_axis_descendants(self):
        children = [*self.root.find_all('**')]
        self.assertListEqual([*self.root.walk_descendants()], children)

    def test_axis_leaves(self):
        expected = [*(d for d in self.root.walk_descendants() if len(d.children) == 0)]
        actual = [*self.root.find_all('***')]
        self.assertListEqual(expected, actual)

    # endregion