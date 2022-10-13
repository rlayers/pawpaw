import itertools

from segments import Span, Ito
from tests.util import _TestIto


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
        self.assertEqual(s, ito.value())

        f = lambda i: i.__str__() * 2
        ito.value_func = f
        self.assertEqual(f, ito.value_func)
        self.assertEqual(s * 2, ito.value())

        ito.value_func = None
        self.assertIsNone(ito.value_func)
        self.assertEqual(s, ito.value())

    def test_children(self):
        i = Ito('abc')
        self.assertIsNotNone(i.children)

    # endregion

    # region __x__ methods
    
    def test_eq_simple(self):
        s = 'abc'
        i1 = Ito(s, 1, -1, 'd')
        
        for s2 in '', i1.string:
            for start in None, i1.start:
                for stop in None, i1.stop:
                    for d in None, i1.desc:
                        i2 = Ito(s2, start, stop, d)
                        with self.subTest(first=i1, second=i2):
                            if i1.string == i2.string and i1.desc == i2.desc and i1.span == i2.span:
                                self.assertEqual(i1, i2)
                            else:
                                self.assertNotEqual(i1, i2)
                                
    def test_eq_derived(self):
        s = 'abc'
        i1 = Ito(s, 1, -1, 'd')
        i2 = self.IntIto(s, *i1.span, i1.desc)
        self.assertNotEqual(i1, i2)

    def test_eq_value_func(self):
        s = 'abc'
        f1 = lambda ito: ito[:].strip()
        f2 = lambda ito: ito[:].upper()
        
        i1 = Ito(s, 1, -1, 'd')
        i2 = i1.clone()
        self.assertEqual(i1, i2)        

        i2.value_func = f1
        self.assertNotEqual(i1, i2)        

        i1.value_func = f1
        self.assertEqual(i1, i2)        

        i2.value_func = f2
        self.assertNotEqual(i1, i2)        

        i1.value_func = f2
        self.assertEqual(i1, i2)        

        i2.value_func = None
        self.assertNotEqual(i1, i2)        

        i1.value_func = None
        self.assertEqual(i1, i2)        

    def test_repr(self):
        s = 'x123x'
        span = 1, -1
        start, stop = Span.from_indices(s, *span)
        desc = 'd'
        ito = Ito(s, *span, desc)
        
        expected = f'Ito({s.__repr__()}, {start}, {stop}, {desc.__repr__()})'
        actual = ito.__repr__()
        self.assertEqual(expected, actual)
        
        self.assertEqual(ito, eval(actual))
    
    def test_str(self):
        s = 'x123x'
        i = Ito(s, 1, -1)
        self.assertEqual(s[1:-1], i.__str__())
        self.assertEqual(s[1:-1], i[:])
        self.assertEqual(s[1:-1], f'{i}')
    
    def test_value(self):
        f = lambda ito: int(ito[:])
        s = 'x123x'
        
        i = Ito(s, 1, -1)
        self.assertEqual(i[:], i.value())
        
        i.value_func = f
        self.assertEqual(i.value_func, f)
        self.assertEqual(f(i[:]), i.value())
        
        i.value_func = None
        self.assertIsNone(i.value_func)
        self.assertEqual(i[:], i.value())
    
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
        self.assertListEqual(grandchildren, [*joined.children])

    # endregion