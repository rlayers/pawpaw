import itertools

import regex
from pawpaw import Ito
from tests.util import _TestIto

class TestItoDescend(_TestIto):
    def test_descends_from(self):
        root = Ito('abcde')
        root.children.add(c := Ito(root, 1, -1))
        c.children.add(gc := Ito(c, 1, -1))

        for desc, basis, expected in (
            ('root', root, False),
            ('child', c, True),
            ('grandchild', gc, True),
        ):
            with self.subTest(desc=f'{desc}.descends_from(root) is {expected}'):
                self.assertEqual(expected, basis.descends_from(root))

            with self.subTest(desc=f'{desc}.clone().descends_from(root) is False'):
                self.assertFalse(basis.clone().descends_from(root))

    def test_has_descendant(self):
        root = Ito('abcde')
        root.children.add(c := Ito(root, 1, -1))
        c.children.add(gc := Ito(c, 1, -1))

        for desc, basis, expected in (
            ('root', root, False),
            ('child', c, True),
            ('grandchild', gc, True),
        ):
            with self.subTest(desc=f'root.has_descendant({desc}) is {expected}'):
                self.assertEqual(expected, root.has_descendant(basis))

            with self.subTest(desc=f'root.has_descendant({desc}.clone) is False'):
                self.assertFalse(root.has_descendant(basis.clone()))                
