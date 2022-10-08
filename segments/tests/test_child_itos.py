import random
import string as py_string

from segments import Ito
from segments.tests.util import _TestIto, RandSpans


# region add
class TestChildItos(_TestIto):
    def test_add_one(self):
        string = 'abcdef'
        parent = Ito(string, desc='parent')
        child = parent.clone(1, desc='child')
        parent.children.add(child)
        self.assertEqual(1, len(parent.children))
        self.assertIs(child, parent.children[0])

    def test_add_several_ordered(self):
        string = 'abcdef'
        parent = Ito(string, desc='parent')
        self.add_chars_as_children(parent, desc='child')
        self.assertEqual(len(string), len(parent.children))
        for i, c in enumerate(parent.children):
            self.assertEqual(string[i], c.__str__())

    def test_add_several_unordered(self):
        string = 'abcdef'
        parent = Ito(string, desc='parent')
        self.add_chars_as_children(parent, desc='child')
        children = [*parent.children]
        parent.children.clear()
        random.shuffle(children)
        for c in children:
            parent.children.add(c)
        self.assertEqual(len(string), len(parent.children))
        for i, c in enumerate(parent.children):
            self.assertEqual(string[i], c.__str__())

    def test_add_generator_ordered(self):
        string = 'abcdef'
        parent = Ito(string, desc='parent')
        g = (parent.clone(i, i + 1, 'Child') for i in range(parent.start, parent.stop))
        parent.children.add(*g)
        self.assertEqual(len(string), len(parent.children))
        for i, c in enumerate(parent.children):
            self.assertEqual(string[i], c.__str__())

    def test_add_generator_reverse_order(self):
        string = 'abcdef'
        parent = Ito(string, desc='parent')
        g = (parent.clone(i, i + 1, 'Child') for i in range(len(string) - 1, -1, -1))
        parent.children.add(*g)
        self.assertEqual(len(string), len(parent.children))
        for i, c in enumerate(parent.children):
            self.assertEqual(string[i], c.__str__())

    def test_add_hierarchical(self):
        string = ' ' * 4096
        root = Ito(string, desc='root')
        levels = 20
        parents = [root]

        # Add ordered
        for i in range(1, levels):
            next_parents = []
            for parent in parents:
                j = max(1, len(parent) // 5)
                rs = RandSpans((j, j + 2), (0, 2))
                children = [parent.clone(*s) for s in rs.generate(string, *parent.span)]
                parent.children.add(*children)
                next_parents.extend(children)
            parents = next_parents

        # Add shuffled
        descendants = [*root.walk_descendants()]
        root.children.clear()
        for d in descendants:
            d.children.clear()
        random.shuffle(descendants)
        root.children.add_hierarchical(*descendants)

    def test_del_key_int(self):
        string = py_string.ascii_lowercase
        parent = Ito(string, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.subTest(position='start'):
            child = parent.children[0]
            del parent.children[0]
            self.assertIsNone(child.parent)
            self.assertEqual(len(string)-1, len(parent.children))
            self.assertEqual('b', parent.children[0].__str__())

        with self.subTest(position='end'):
            child = parent.children[-1]
            del parent.children[-1]
            self.assertIsNone(child.parent)
            self.assertEqual(len(string)-2, len(parent.children))
            self.assertEqual('y', parent.children[-1].__str__())

        with self.subTest(position='middle'):
            child = next(i for i in parent.children if i.__str__() == 'h')
            i = parent.children.index(child)
            del parent.children[i]
            self.assertIsNone(child.parent)
            self.assertEqual(len(string)-3, len(parent.children))
            self.assertEqual('g', parent.children[i-1].__str__())
            self.assertEqual('i', parent.children[i].__str__())

    def test_del_key_slice(self):
        string = py_string.ascii_lowercase
        parent = Ito(string, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.subTest(position='start'):
            children = parent.children[:2]
            del parent.children[:2]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(string)-2, len(parent.children))
            self.assertEqual('c', parent.children[0].__str__())

        with self.subTest(position='end'):
            children = parent.children[-2:]
            del parent.children[-2:]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(string)-4, len(parent.children))
            self.assertEqual('x', parent.children[-1].__str__())

        with self.subTest(position='middle'):
            c = next(i for i in parent.children if i.__str__() == 'h')
            i = parent.children.index(c)
            children = parent.children[i:i+2]
            del parent.children[i:i+2]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(string) - 6, len(parent.children))
            self.assertEqual('g', parent.children[i-1].__str__())
            self.assertEqual('j', parent.children[i].__str__())

    def test_indexer_set_key_int_invalid(self):
        string = py_string.ascii_lowercase
        parent = Ito(string, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.assertRaises(TypeError):
            parent.children[0] = 'abc'

    def test_indexer_set_key_int(self):
        string = py_string.ascii_lowercase
        parent = Ito(string, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.subTest(position='start'):
            child = parent.children[0]
            del parent.children[0]
            self.assertIsNone(child.parent)
            self.assertEqual(len(string)-1, len(parent.children))
            parent.children[0] = child
            self.assertEqual(len(string)-1, len(parent.children))
            self.assertEqual('a', parent.children[0].__str__())

        with self.subTest(position='end'):
            child = parent.children[-1]
            del parent.children[-1]
            self.assertIsNone(child.parent)
            self.assertEqual(len(string)-2, len(parent.children))
            parent.children[-1] = child
            self.assertEqual(len(string)-2, len(parent.children))
            self.assertEqual('z', parent.children[-1].__str__())

        with self.subTest(position='middle'):
            child = next(i for i in parent.children if i.__str__() == 'h')
            i = parent.children.index(child)
            del parent.children[i]
            self.assertIsNone(child.parent)
            self.assertEqual(len(string)-3, len(parent.children))
            parent.children[i] = child
            self.assertEqual(len(string)-3, len(parent.children))
            self.assertEqual('h', parent.children[i].__str__())

    def test_indexer_set_key_slice(self):
        string = py_string.ascii_lowercase
        parent = Ito(string, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.subTest(position='start'):
            children = parent.children[:2]
            del parent.children[:2]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(string)-2, len(parent.children))
            parent.children[:2] = children[0], children[1]
            self.assertEqual(len(string)-2, len(parent.children))
            self.assertEqual('a', parent.children[0].__str__())
            self.assertEqual('b', parent.children[1].__str__())
            self.assertEqual('e', parent.children[2].__str__())

        with self.subTest(position='end'):
            children = parent.children[-2:]
            del parent.children[-2:]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(string)-4, len(parent.children))
            parent.children[-2:] = children[0], children[1]
            self.assertEqual(len(string)-4, len(parent.children))
            self.assertEqual('z', parent.children[-1].__str__())
            self.assertEqual('y', parent.children[-2].__str__())
            self.assertEqual('v', parent.children[-3].__str__())

        with self.subTest(position='middle'):
            c = next(i for i in parent.children if i.__str__() == 'h')
            i = parent.children.index(c)
            children = parent.children[i:i+2]
            del parent.children[i:i+2]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(string)-6, len(parent.children))
            parent.children[i:i+4] = children[0], children[1]
            self.assertEqual(len(string)-8, len(parent.children))
            self.assertEqual('h', parent.children[i].__str__())
            self.assertEqual('i', parent.children[i+1].__str__())
            self.assertEqual('n', parent.children[i+2].__str__())
