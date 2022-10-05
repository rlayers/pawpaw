import itertools
import warnings

import regex
from segments import Ito, slice_indices_to_span
from segments.tests.util import _TestIto, RandSubstrings


class TestIto(_TestIto):
    def test_normalize_valid(self):
        string = ' abc '
        for basis in (len(string), string):
            with self.subTest(basis=basis):
                for start in (-100, -1, None, 0, 1, 100):
                    with self.subTest(start=start):
                        for stop in (-100, -1, None, 0, 1, 100):
                            with self.subTest(stop=stop):
                                _slice = slice(start, stop)
                                i, j = slice_indices_to_span(string, start, stop)
                                self.assertEqual(string[_slice], string[i:j])

        basis = 1.0
        with self.subTest(basis=basis):
            with self.assertRaises(TypeError):
                slice_indices_to_span(basis, 1)

    #endregion

    #region Ctors

    def test_ctor_string_only(self):
        for string in None, '', 'a', 'abc':
            with self.subTest(string=string):
                if string is None:
                    with self.assertRaises(ValueError):
                        Ito(None)
                else:
                    ito = Ito(string)
                    self.assertEqual(string, ito.string)

    def test_ctor_indices_default(self):
        string = 'abc'
        for start in None, 0:
            with self.subTest(start=start):
                for stop in None, len(string):
                    with self.subTest(stop=stop):
                        ito = Ito(string, start, stop)
                        self.assertEqual(0, ito.start)
                        self.assertEqual(len(string), ito.stop)

    def test_ctor_indices_non_defaults(self):
        string = 'abcd'
        indices = -100, *range(-3, 3), 100
        for start in indices:
            with self.subTest(start=start):
                for stop in indices:
                    with self.subTest(stop=stop):
                        sliced = string[start:stop]
                        ito = Ito(string, start, stop)
                        self.assertLessEqual(0, ito.start)
                        self.assertGreaterEqual(len(string), ito.stop)
                        self.assertEqual(sliced, ito.__str__())

    def test_clone_basic(self):
        string = 'abc'
        d = 'x'
        ito = Ito(string, 1, 2, descriptor=d)

        params = [
            {
            },
            {
                'start': 0,
            },
            {
                'start': 0,
                'stop': len(string),
            },
            {
                'stop': len(string),
            },
            {
                'start': 0,
                'stop': len(string),
                'descriptor': 'z'
            }
        ]

        for pdict in params:
            with self.subTest(**pdict):
                expected = Ito(
                    string,
                    pdict.get('start', ito.start),
                    pdict.get('stop', ito.stop),
                    pdict.get('descriptor', ito.descriptor),
                )
                clone = ito.clone(**pdict)
                self.assertEqual(expected, clone)

    def test_clone_children(self):
        s = 'abc'
        parent = Ito(s, descriptor='parent')
        self.add_chars_as_children(parent, 'child')

        for oc in (True, False):
            with self.subTest(omit_children=oc):
                clone = parent.clone(omit_children=oc)
                self.assertEqual(parent, clone)
                self.assertEqual(len(s), len(parent.children))
                if oc:
                    self.assertEqual(0, len(clone.children))
                else:
                    self.assertEqual(len(parent.children), len(clone.children))

    def test_clone_with_value_funcs(self):
        string = ' abcdef '
        f1 = lambda ito: ito.__str__().strip()
        f2 = lambda ito: ito.__str__().upper()

        root = Ito(string)
        self.assertEqual(string, root.__value__())

        clone = root.clone()
        self.assertEqual(string, clone.__value__())

        root.value_func = f1
        self.assertEqual(f1(root), root.__value__())
        self.assertEqual(string, clone.__value__())  # Ensure clone didn't change

        clone.value_func = f2
        self.assertEqual(f2(clone), clone.__value__())
        self.assertEqual(f1(root), root.__value__())  # Ensure root didn't change

        root.value_func = None
        self.assertEqual(string, root.__value__())
        self.assertEqual(f2(clone), clone.__value__())  # Ensure clone didn't change

    def test_offset(self):
        string = 'abc'
        d = 'x'
        ito = Ito(string, 1, 2, descriptor=d)

        params = [
            {
                'start': -1,
            },
            {
                'start': -10,
            },
            {
                'start': -1,
                'stop': 1,
            },
            {
                'start': -20,
                'stop': 1,
            },
            {
                'stop': 1,
            },
            {
                'stop': 10,
            },
            {
                'start': -1,
                'stop': 20,
            },
            {
                'start': -1,
                'stop': 1,
                'descriptor': 'z'
            }
        ]

        for pdict in params:
            with self.subTest(**pdict):
                expected = Ito(
                    string,
                    ito.start + pdict.get('start', 0),
                    ito.stop + pdict.get('stop', 0),
                    pdict.get('descriptor', ito.descriptor)
                )

                t_start = ito.start + pdict.get('start', 0)
                t_stop = ito.stop + pdict.get('stop', 0)
                with warnings.catch_warnings(record=True) as w:
                    offset = ito.offset(**pdict)
                    self.assertEqual(expected, offset)
                if not(0 <= t_start <= len(string) and 0 <= t_stop <= len(string)):
                    self.assertIsNotNone(w)

    def test_slice(self):
        string = ' abc '
        d = 'x'
        ito = Ito(string, 1, -1, descriptor=d)

        params = [
            {
                'start': -1,
            },
            {
                'start': -100,
            },
            {
                'start': -1,
                'stop': 1,
            },
            {
                'stop': 1,
            },
            {
                'start': -100,
                'stop': 1,
            },
            {
                'start': -100,
                'stop': 100,
            },
            {
                'start': -1,
                'stop': 1,
                'descriptor': 'z'
            }
        ]

        for pdict in params:
            with self.subTest(**pdict):
                temp = Ito(ito.__str__(), **pdict)
                sliced = ito.slice(**pdict)
                self.assertEqual(temp.__str__(), sliced.__str__())

    def test_from_match(self):
        first = 'John'
        last = 'Doe'
        string = ' '.join((first, last))
        re = regex.compile(r'(?P<fn>.+)\s(?P<ln>.+)')
        m = re.fullmatch(string)

        desc = 'x'
        with self.subTest(group='Absent'):
            ito = Ito.from_match(m, descriptor=desc)
            self.assertEqual(m.group(), ito.__str__())
            self.assertEqual(desc, ito.descriptor)

        for group in 0, 1, 'fn', 2, 'ln':
            with self.subTest(group=group):
                ito = Ito.from_match(m, group, descriptor=desc)
                self.assertEqual(m.group(group), ito.__str__())
                self.assertEqual(desc, ito.descriptor)

    def test_from_substrings(self):
        string = 'abcd' * 10
        string = f' {string} '

        with self.subTest(spacing='Consecutive'):
            for size in ((1, 1), (2, 2), (1, 3), (2, 3)):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, (0, 0))
                    subs = [*rs.generate(string, 1, -1)]
                    itos = Ito.from_substrings(string, *subs)
                    self.assertListEqual(subs, [i.__str__() for i in itos])

        with self.subTest(spacing='Gaps'):
            for size in ((1, 1), (2, 2), (1, 3), (2, 3)):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, (1, 2))
                    subs = [*rs.generate(string, 1, -1)]
                    itos = Ito.from_substrings(string, *subs)
                    self.assertListEqual(subs, [i.__str__() for i in itos])

        with self.subTest(spacing='Overlaps'):
            for size in ((3, 3),):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, (-1, -1))
                    subs = [*rs.generate(string, 1, -1)]
                    with self.assertRaises(Exception):
                        itos = [*Ito.from_substrings(string, *subs)]

    #endregion

    #region properties

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
        span = (1, 2)
        i = Ito(s, *span)
        self.assertEqual(span[0], i.start)

    def test_stop(self):
        s = 'abc'
        span = (1, 2)
        i = Ito(s, *span)
        self.assertEqual(span[1], i.stop)

    def test_valid_parent(self):
        s = 'abc'
        i1 = Ito(s)
        i2 = i1.clone(1, 2)
        i2._set_parent(i1)
        self.assertEqual(i1, i2.parent)

    def test_invalid_parent(self):
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

    #endregion

    #region __x__ methods

    #endregion

    #region combinatorics

    def test_join(self):
        s = 'abc 123'
        joined_desc = 'joined'

        children = [*Ito.from_substrings(s, *s.split(' '), descriptor='children')]
        for child in children:
            child.children.add(*Ito.from_substrings(s, *child.__str__(), descriptor='grandchild'))
        grandchildren = [*itertools.chain.from_iterable(ito.children for ito in children)]

        joined = Ito.join(*children, descriptor=joined_desc)
        self.assertIsNot(joined, children[0])
        self.assertIsNot(joined, children[1])
        self.assertEqual(s, joined.__str__())
        self.assertEqual(joined_desc, joined.descriptor)
        self.assertEqual(len(grandchildren), len(joined.children))
        for gc1, gc2 in zip(grandchildren, joined.children):
            self.assertEqual(gc1, gc2)

    #endregion

    #region children

    #region __x__ methods

    def test__str__(self):
        for string in '', 'a', 'abc':
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertIsInstance(ito.__str__(), str)
                self.assertEqual(string, ito.__str__())

    def test__len__(self):
        for string in '', 'a', 'abc':
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertIsInstance(len(ito), int)
                self.assertEqual(len(string), len(ito))

    #endregion
