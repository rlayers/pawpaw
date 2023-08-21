import random
import string as py_string

from pawpaw import Ito, Span, visualization
from tests.util import _TestIto, RandSpans


class TestChildItos(_TestIto):
    # region add

    def test_add_one(self):
        s = 'abcdef'
        parent = Ito(s, desc='parent')
        child = parent.clone(1, desc='child')
        parent.children.add(child)
        self.assertSequenceEqual([child], parent.children)
        self.assertIs(child, parent.children[0])

    def test_add_several_ordered(self):
        s = 'abcdef'
        parent = Ito(s, desc='parent')
        self.add_chars_as_children(parent, desc='child')
        self.assertSequenceEqual(s, [str(i) for i in parent.children])

    def test_add_several_unordered(self):
        s = 'abcdef'
        parent = Ito(s, desc='parent')
        self.add_chars_as_children(parent, desc='child')
        children = [*parent.children]
        parent.children.clear()
        random.shuffle(children)
        for c in children:
            parent.children.add(c)
        self.assertSequenceEqual(s, [str(i) for i in parent.children])

    def test_add_generator_ordered(self):
        s = 'abcdef'
        parent = Ito(s, desc='parent')
        g = (parent.clone(i, i + 1, 'Child') for i in range(parent.start, parent.stop))
        parent.children.add(*g)
        self.assertSequenceEqual(s, [str(i) for i in parent.children])

    def test_add_generator_reverse_order(self):
        s = 'abcdef'
        parent = Ito(s, desc='parent')
        g = (parent.clone(i, i + 1, 'Child') for i in range(len(s) - 1, -1, -1))
        parent.children.add(*g)
        self.assertSequenceEqual(s, [str(i) for i in parent.children])

    #endregion

    # region remove

    def test_remove_non_contiguous_descendants(self):
        s = " one two three "
        counter = 0
        root = Ito(s, 1, -2, str(counter))

        for word in root.str_split():
            word.desc = str(counter := counter + 1)
            root.children.add(word)
            for c in word:
                c.desc = str(counter := counter + 1)
                word.children.add(c)

        for i in root.walk_descendants(reverse=True):
            i.parent.children.remove(i)

    def test_remove_contiguous_descendants(self):
        s = ' abc '
        root = Ito(s, 1, -1, desc='root')
        counter = 0
        adds = list[Ito]()
        for i in range(0, 5):
            adds.extend(i.clone(desc=(str(counter := counter + 1))) for i in root)
        root.children.add_hierarchical(*adds)

        for i in root.walk_descendants(reverse=True):
            i.parent.children.remove(i)

    #endregion

    # region add hierarchical

    def test_add_hierarchical_rand(self):
        s = ' ' * 2048
        root = Ito(s, desc='root')
        levels = 10
        parents = [root]

        # Add ordered
        for i in range(1, levels):
            next_parents = []
            for parent in parents:
                j = max(1, len(parent) // 5)
                rs = RandSpans(Span(j, j + 2), Span(0, 2))
                children = [parent.clone(*s) for s in rs.generate(s, *parent.span)]
                parent.children.add(*children)
                next_parents.extend(children)
            parents = next_parents
            
        # Save and clear
        ordered_descendants = [*root.walk_descendants()]
        root.children.clear()
        for d in ordered_descendants:
            d.children.clear()
        shuffled_descendants = list.copy(ordered_descendants)
        random.shuffle(shuffled_descendants)

        # Add shuffled and compare
        root.children.add_hierarchical(*shuffled_descendants)
        self.assertSequenceEqual(ordered_descendants, [*root.walk_descendants()])

        self.assertTrue(all(i.parent is not None for i in root.walk_descendants()))

    def test_add_hierarchical_interleaved(self):
        s = '012345543210'
        
        i1 = Ito(s) # 0..0
        i1.children.add(c := Ito(s, 2, -2))  # 2..2
        c.children.add(Ito(s, 4, -4))  # 4..4

        i2 = Ito(s, 1, -1)  # 1..1
        i2.children.add(c := Ito(s, 3, -3))  # 3..3
        c.children.add(Ito(s, 5, -5))  # 3..3

        i1.children.add_hierarchical(i2)

        ito = i1
        for i in range(1, 6):
            ito = ito.children[0]
            self.assertTrue(ito.str_startswith(str(i)))
            self.assertTrue(ito.str_endswith(str(i)))

    def test_add_hierarchical_with_key(self):
        s = ' abc '
        root = Ito(s, 1, -1, desc='root')

        adds = {}
        adds['low to high'] = (lst := list[Ito]())
        for i in range(0, 10):
            lst.append(root.clone(desc=str(i)))
        
        adds['high to low'] = lst[::-1]

        adds['shuffled'] = [*lst]
        random.shuffle(adds['shuffled'])

        for adds_k, adds_l in adds.items():
            for key_str in None, 'lambda ito: int(ito.desc)':
                key_lam = None if key_str is None else eval(key_str)

                with self.subTest(adds_sort=adds_k, key=key_str):
                    root_clone = root.clone()
                    adds_clone = [a.clone() for a in adds_l]
                    root_clone.children.add_hierarchical(*adds_clone, key=key_lam)
                    descs = [*root_clone.walk_descendants()]
                    if key_str is None:
                        self.assertListEqual(adds_l, descs)
                    else:
                        self.assertListEqual(lst, descs)

    #endregion

    # region del

    def test_del_key_int(self):
        s = py_string.ascii_lowercase
        parent = Ito(s, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.subTest(position='start'):
            child = parent.children[0]
            del parent.children[0]
            self.assertIsNone(child.parent)
            self.assertEqual(len(s)-1, len(parent.children))
            self.assertEqual('b', str(parent.children[0]))

        with self.subTest(position='end'):
            child = parent.children[-1]
            del parent.children[-1]
            self.assertIsNone(child.parent)
            self.assertEqual(len(s)-2, len(parent.children))
            self.assertEqual('y', str(parent.children[-1]))

        with self.subTest(position='middle'):
            child = next(i for i in parent.children if str(i) == 'h')
            i = parent.children.index(child)
            del parent.children[i]
            self.assertIsNone(child.parent)
            self.assertEqual(len(s)-3, len(parent.children))
            self.assertEqual('g', str(parent.children[i-1]))
            self.assertEqual('i', str(parent.children[i]))

    def test_del_key_slice(self):
        s = py_string.ascii_lowercase
        parent = Ito(s, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.subTest(position='start'):
            children = parent.children[:2]
            del parent.children[:2]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(s)-2, len(parent.children))
            self.assertEqual('c', str(parent.children[0]))

        with self.subTest(position='end'):
            children = parent.children[-2:]
            del parent.children[-2:]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(s)-4, len(parent.children))
            self.assertEqual('x', str(parent.children[-1]))

        with self.subTest(position='middle'):
            c = next(i for i in parent.children if str(i) == 'h')
            i = parent.children.index(c)
            children = parent.children[i:i+2]
            del parent.children[i:i+2]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(s) - 6, len(parent.children))
            self.assertEqual('g', str(parent.children[i-1]))
            self.assertEqual('j', str(parent.children[i]))

    # endregion

    # region set

    def test_indexer_set_key_int_invalid(self):
        s = py_string.ascii_lowercase
        parent = Ito(s, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.assertRaises(TypeError):
            parent.children[0] = 'abc'

    def test_indexer_set_key_int(self):
        s = py_string.ascii_lowercase
        parent = Ito(s, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.subTest(position='start'):
            child = parent.children[0]
            del parent.children[0]
            self.assertIsNone(child.parent)
            self.assertEqual(len(s)-1, len(parent.children))
            parent.children[0] = child
            self.assertEqual(len(s)-1, len(parent.children))
            self.assertEqual('a', str(parent.children[0]))

        with self.subTest(position='end'):
            child = parent.children[-1]
            del parent.children[-1]
            self.assertIsNone(child.parent)
            self.assertEqual(len(s)-2, len(parent.children))
            parent.children[-1] = child
            self.assertEqual(len(s)-2, len(parent.children))
            self.assertEqual('z', str(parent.children[-1]))

        with self.subTest(position='middle'):
            child = next(i for i in parent.children if str(i) == 'h')
            i = parent.children.index(child)
            del parent.children[i]
            self.assertIsNone(child.parent)
            self.assertEqual(len(s)-3, len(parent.children))
            parent.children[i] = child
            self.assertEqual(len(s)-3, len(parent.children))
            self.assertEqual('h', str(parent.children[i]))

    def test_indexer_set_key_slice(self):
        s = py_string.ascii_lowercase
        parent = Ito(s, desc='parent')
        self.add_chars_as_children(parent, desc='child')

        with self.subTest(position='start'):
            children = parent.children[:2]
            del parent.children[:2]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(s)-2, len(parent.children))
            parent.children[:2] = children[0], children[1]
            self.assertEqual(len(s)-2, len(parent.children))
            self.assertEqual('a', str(parent.children[0]))
            self.assertEqual('b', str(parent.children[1]))
            self.assertEqual('e', str(parent.children[2]))

        with self.subTest(position='end'):
            children = parent.children[-2:]
            del parent.children[-2:]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(s)-4, len(parent.children))
            parent.children[-2:] = children[0], children[1]
            self.assertEqual(len(s)-4, len(parent.children))
            self.assertEqual('z', str(parent.children[-1]))
            self.assertEqual('y', str(parent.children[-2]))
            self.assertEqual('v', str(parent.children[-3]))

        with self.subTest(position='middle'):
            c = next(i for i in parent.children if str(i) == 'h')
            i = parent.children.index(c)
            children = parent.children[i:i+2]
            del parent.children[i:i+2]
            for child in children:
                self.assertIsNone(child.parent)
            self.assertEqual(len(s)-6, len(parent.children))
            parent.children[i:i+4] = children[0], children[1]
            self.assertEqual(len(s)-8, len(parent.children))
            self.assertEqual('h', str(parent.children[i]))
            self.assertEqual('i', str(parent.children[i+1]))
            self.assertEqual('n', str(parent.children[i+2]))

    # endregion
