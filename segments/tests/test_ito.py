import itertools
import warnings

import regex
from segments import Span, Ito
from segments.tests.util import _TestIto, RandSubstrings


class TestIto(_TestIto):
    # region properties

    def test_string(self):
        s = 'abc'
        i = Ito(s)
        self.assertEqual(s, i.string)

    def test_span(self):
        s = 'abc'
        span = (1, 2)
        i = Ito(s, *span)
        self.assertEqual(span, i.span)

    def test_start(self):
        s = 'abc'
        span = Span(1, 2)
        i = Ito(s, *span)
        self.assertEqual(span.start, i.start)

    def test_stop(self):
        s = 'abc'
        span = Span(1, 2)
        i = Ito(s, *span)
        self.assertEqual(span.stop, i.stop)

    def test_set_parent_valid(self):
        s = 'abc'
        i1 = Ito(s)
        i2 = i1.clone(1, 2)
        i2._set_parent(i1)
        self.assertEqual(i1, i2.parent)

    def test_set_parent_invalid_parent(self):
        s = '__abc__'
        i1 = Ito(s, 1, -1)

        with self.subTest(scenario='different string'):
            i2 = Ito(s[1:])
            with self.assertRaises(ValueError):
                i2._set_parent(i1)

        with self.subTest(scenario='incompatible start'):
            i2 = Ito(s, stop=-1)
            with self.assertRaises(ValueError):
                i2._set_parent(i1)

        with self.subTest(scenario='incompatible stop'):
            i2 = Ito(s, 1)
            with self.assertRaises(ValueError):
                i2._set_parent(i1)

        with self.subTest(scenario='parent as self'):
            with self.assertRaises(ValueError):
                i1._set_parent(i1)

    def test_value_func(self):
        s = 'abc'
        ito = Ito(s)

        self.assertIsNone(ito.value_func)
        self.assertEqual(s, ito.__value__())

        f = lambda i: i.__str__() * 2
        ito.value_func = f
        self.assertEqual(f, ito.value_func)
        self.assertEqual(s * 2, ito.__value__())

        ito.value_func = None
        self.assertIsNone(ito.value_func)
        self.assertEqual(s, ito.__value__())

    def test_children(self):
        i = Ito('abc')
        self.assertIsNotNone(i.children)

    # endregion

    # region __x__ methods

    def test_repr(self):
        s = 'x123x'
        span = 1, -1
        start, stop = Span.from_indices(s, *span)
        desc = 'd'
        ito = Ito(s, *span, desc)
        
        expected = f'segments.Ito({s.__repr__()}, {start}, {stop}, {desc.__repr__()})'
        actual = ito.__repr__()
        self.assertEqual(expected, actual)
        
        i = actual.index('.')
        self.assertEqual(ito, eval(actual[i+1:]))
    
    def test_str(self):
        s = 'x123x'
        i = Ito(s, 1, -1)
        self.assertEqual(s[1:-1], f'{i}')
    
    def test_value(self):
        pass
    
    def test_len(self):
        s = 'x123x'
        i = Ito(s, 1, -1)
        self.assertEqual(3, len(i))
    
    def test_getitem(self):
        s = 'x123x'
        i = Ito(s, 1, -1)
        self.assertEqual('1', i[0])
        self.assertEqual('3', i[-1])
        self.assertEqual('123', i[:])
        self.assertEqual('23', i[1:])
        self.assertEqual('2', i[1:-1])
        self.assertEqual('12', i[:-1])

        with self.assertRaises(TypeError):
            self.assertEqual('2', i['1'])
            
    # endregion

    # region combinatorics

    def test_join(self):
        s = 'abc 123'
        joined_desc = 'joined'

        children = [*Ito.from_substrings(s, *s.split(), desc='children')]
        for child in children:
            child.children.add(*Ito.from_substrings(s, *child.__str__(), desc='grandchild'))
        grandchildren = [*itertools.chain.from_iterable(ito.children for ito in children)]

        joined = Ito.join(*children, desc=joined_desc)
        self.assertIsNot(joined, children[0])
        self.assertIsNot(joined, children[1])
        self.assertEqual(s, joined.__str__())
        self.assertEqual(joined_desc, joined.desc)
        self.assertEqual(len(grandchildren), len(joined.children))
        for gc1, gc2 in zip(grandchildren, joined.children):
            self.assertEqual(gc1, gc2)

    # endregion
