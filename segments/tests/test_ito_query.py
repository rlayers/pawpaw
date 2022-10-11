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

        self.leaf = self.root
        while len(self.leaf.children) > 0:
            self.leaf = self.leaf.children[0]

    # region axis

    def test_axis_root(self):
        i = self.root.find('....')
        self.assertIs(self.root, i)

        for order in 'n', 'r':
            with self.subTest(order=order):
                i = self.leaf.find('....' + order)
                self.assertEqual(self.root, i)

    def test_axis_ancestors(self):
        expected = [self.leaf.parent]
        while expected[0].parent is not None:
            expected.insert(0, expected[0].parent)

        for order in 'n', 'r':
            with self.subTest(order=order):
                actual = [*self.leaf.find_all('...' + order)]
                self.assertListEqual(expected, actual)
                expected.reverse()

    def test_axis_parent(self):
        i = self.root.find('..')
        self.assertIsNone(i)

        last = self.root
        while len(last.children) > 0:
            cur = last.children[0]
            self.assertEqual(last, cur.find('..'))
            last = cur

    def test_axis_self(self):
        for order in 'n', 'r':
            with self.subTest(order=order):
                i = self.root.find('.' + order)
                self.assertIs(self.root, i)
                i = self.leaf.find('.' + order)
                self.assertIs(self.leaf, i)

    def test_axis_children(self):
        order = 'n'
        with self.subTest(order=order):
            expected = [*self.root.children]
            actual = [*self.root.find_all('*' + order)]
            self.assertListEqual(expected, actual)

        order = 'r'
        with self.subTest(order=order):
            expected.reverse()
            actual = [*self.root.find_all('*' + order)]
            self.assertListEqual(expected, actual)

    def test_axis_descendants(self):
        order = 'n'
        with self.subTest(order=order):
            expected = [*self.root.find_all('**' + order)]
            self.assertListEqual([*self.root.walk_descendants()], expected)

        order = 'r'
        with self.subTest(order=order):
            expected.reverse()
            actual = [*self.root.find_all('**' + order)]
            self.assertListEqual(expected, actual)

    def test_axis_leaves(self):
        order = 'n'
        with self.subTest(order=order):
            expected = [*(d for d in self.root.walk_descendants() if len(d.children) == 0)]
            actual = [*self.root.find_all('***' + order)]
            self.assertListEqual(expected, actual)

        order = 'r'
        with self.subTest(order=order):
            expected.reverse()
            actual = [*self.root.find_all('***' + order)]
            self.assertListEqual(expected, actual)

    # endregion