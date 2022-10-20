from segments import Ito
from segments.itorator import Reflect, Wrap
from tests.util import _TestIto


class TestItorator(_TestIto):
    """Uses Reflect and Wrap classes, which have trivial implementation, to test base class functionality"""
    def test_traverse(self):
        s = 'abc'
        root = Ito(s)
        self.add_chars_as_children(root, 'Child')

        reflect = Reflect()
        rv = [*reflect.traverse(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertEqual(root, ito)
        self.assertEqual([*root.children], [*ito.children])

    def test_traverse_with_next(self):
        s = 'abc'
        root = Ito(s)
        self.add_chars_as_children(root, 'Child')

        reflect = Reflect()
        apply_desc = 'x'
        reflect.itor_next = Wrap(lambda ito: (ito.clone(desc=apply_desc),))
        rv = [*reflect.traverse(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertEqual(apply_desc, ito.desc)
        self.assertEqual([*root.children], [*ito.children])

    def test_traverse_with_children(self):
        s = 'abc'
        root = Ito(s)

        reflect = Reflect()
        apply_desc = 'x'
        reflect.itor_children = Wrap(lambda ito: tuple(ito.clone(i, i+1, apply_desc) for i, c in enumerate(s)))
        rv = [*reflect.traverse(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertSequenceEqual(s, [str(i) for i in ito.children])
        self.assertTrue(all(c.desc == apply_desc for c in ito.children))
        
    def test_traverse_with_carry_through(self):
        s = 'abc'
        root = Ito(s)
        d_changed = 'changed'

        reflect = Reflect()
        make_chars = Wrap(lambda ito: tuple(ito.clone(i, i+1, 'char') for i in range(*ito.span)))
        reflect.itor_children = make_chars
        rename = Wrap(lambda ito: tuple(ito.clone(desc=d_changed) if i.parent is not None else i for i in [ito]))
        make_chars.itor_next = rename
        rv = [*reflect.traverse(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertSequenceEqual(s, [str(i) for i in ito.children])
        self.assertTrue(all(c.desc == d_changed for c in ito.children))
