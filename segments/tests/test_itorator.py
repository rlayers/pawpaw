import typing

from segments import Ito
from segments.itorator import Reflect
from segments.tests.util import _TestIto


class TestItorator(_TestIto):
    """Uses Reflect class, which has trivial implemntation, to test base class functionality"""
    def test_traverse(self):
        s = 'abc'
        root = Ito(s)
        self.add_chars_as_children(root, 'Child')

        reflect = Reflect()
        rv: typing.List[Ito] = [*reflect.traverse(root)]
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertEqual(len(root.children), len(ito.children))
        self.assertEqual(root, ito)

    def test_traverse_with_next(self):
        s = 'abc'
        root = Ito(s)
        self.add_chars_as_children(root, 'Child')

        reflect = Reflect()
        apply_desc = 'x'
        reflect.itor_next = lambda ito: [ito.clone(descriptor=apply_desc)]
        rv: typing.List[Ito] = [*reflect.traverse(root)]
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertEqual(len(root.children), len(ito.children))
        self.assertEqual(apply_desc, ito.descriptor)

    def test_traverse_with_children(self):
        s = 'abc'
        root = Ito(s)

        reflect = Reflect()
        apply_desc = 'x'
        reflect.itor_children = lambda ito: (ito.clone(i, i+1, apply_desc) for i, c in enumerate(s))
        rv: typing.List[Ito] = [*reflect.traverse(root)]
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertEqual(len(s), len(ito.children))
        self.assertTrue(all(c.descriptor == apply_desc for c in ito.children))
