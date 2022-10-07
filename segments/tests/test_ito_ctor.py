import itertools
import warnings

import regex
from segments import Span, Ito
from segments.tests.util import _TestIto, RandSubstrings


class TestItoCtor(_TestIto):
    def test_ctor_invalid_basis(self):
        for basis in None, 1:
            with self.subTest(basis=basis):
                with self.assertRaises(TypeError):
                    Ito(basis)

    def test_ctor_str_defaults(self):
        for basis in '', ' ', 'a', 'abc':
            with self.subTest(basis=basis):
                i = Ito(basis)
                self.assertEquals(s, i.string)
                self.assertEquals(s, i[:])
                self.assertEquals((0, len(s)), i.span)

    def test_ctor_str_non_defaults(self):
        string = 'abcd'
        indices = -100, *range(-3, 3), 100
        for start in indices:
            for stop in indices:
                with self.subTest(bais=s, start=start, stop=stop):
                    ls = len(s)
                    start_t = min(ls, start) if start >= 0 else max(0, ls + start)
                    stop_t = min(ls, stop) if stop >= 0 else max(0, ls + stop)
                    if start_t > stop_t:
                        with self.assertRaises(ValueError):
                            i = Ito(s, start, stop)
                    else:
                        i = Ito(s, start, stop)
                        self.assertLessEqual(0, i.start)
                        self.assertGreaterEqual(ls, i.stop)
                        self.assertEqual(s[start:stop], i[:])

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
