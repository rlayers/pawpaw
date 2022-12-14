import itertools

import regex
from pawpaw import Ito, Span
from tests.util import _TestIto, IntIto, RandSpans, RandSubstrings


class TestItoCtor(_TestIto):
    def test_ctor_invalid_src(self):
        for src in None, 1:
            with self.subTest(src=src):
                with self.assertRaises(TypeError):
                    Ito(src)

    def test_ctor_str_defaults(self):
        for src in '', ' ', 'a', 'abc':
            with self.subTest(src=src):
                i = Ito(src)
                self.assertEqual(src, i.string)
                self.assertEqual(src, str(i))
                self.assertEqual((0, len(src)), i.span)

    def test_ctor_str_non_defaults(self):
        s = 'abcd'
        indices = -100, *range(-3, 3), 100
        for start in indices:
            for stop in indices:
                with self.subTest(bais=s, start=start, stop=stop):
                    i = Ito(s, start, stop)
                    self.assertLessEqual(0, i.start)
                    self.assertGreaterEqual(len(s), i.stop)
                    self.assertEqual(s[start:stop], str(i))
                    
    def test_ctor_ito(self):
        for s in '', ' ', 'a', 'abc', ' abc ':
            for i in None, 0, 1:
                for j in -1, len(s), None:
                    src = Ito(s, i, j)
                    for start, stop in (None, None), (1, None), (None, -1), (1, -1):
                        with self.subTest(src=src, start=start, stop=stop):
                            ito = Ito(src, start, stop)
                            self.assertEqual(src.string, ito.string)
                            self.assertEqual(src[start:stop], ito)

    def test_from_match_group(self):
        first = 'John'
        last = 'Doe'
        string = ' '.join((first, last))
        re = regex.compile(r'(?P<fn>.+)\s(?P<ln>.+)')
        m = re.fullmatch(string)

        for group in None, 0, 1, 'fn', 2, 'ln':
            with self.subTest(group=group):
                if group is None:
                    ito = Ito.from_match_group(m)
                    desc = '0'
                else:
                    ito = Ito.from_match_group(m, group)
                    desc = str(group)
                self.assertEqual(m.group() if group is None else m.group(group), str(ito))
                self.assertEqual(desc, ito.desc)

    def test_from_match_simple(self):
        first = 'John'
        last = 'Doe'
        string = ' '.join((first, last))
        re = regex.compile(r'(?P<fn>.+)\s(?P<ln>.+)')
        m = re.fullmatch(string)

        for exclude_keys in None, [1], ['fn'], [2], ['ln'], ['fn', 2], [1, 'ln']:
            with self.subTest(exclude_keys=exclude_keys):
                if exclude_keys is None:
                    ito = Ito.from_match(m)
                else:
                    ito = Ito.from_match(m, *exclude_keys)

                itos = [ito, *ito.walk_descendants()]

                if exclude_keys is not None:
                    for k in exclude_keys:
                        if k == 0:
                            self.assertIn('0', [i.desc for i in itos])
                        else:
                            self.assertNotIn(k, [i.desc for i in itos])

                for i in itos:
                    k = i.desc
                    if i.desc.isnumeric():
                        k = int(k)
                    self.assertEqual(m.group(k), str(i))

    def test_from_re(self):
        s = 'the quick brown fox'

        re = 'abc'
        with self.subTest(re='abc'):
            with self.assertRaises(TypeError):
                actual = [*Ito.from_re(re, s)]

        re = regex.compile(r'(?<word>\w+)')
        with self.subTest(re=re, limit=None):
            expected = [*Ito.from_substrings(s, s.split(), '0')]
            for e in expected:
                e.children.add(e.clone(desc='word'))
            actual = [*Ito.from_re(re, s)]
            self.assertListEqual(expected, actual)
            for e, a in zip(expected, actual):
                self.assertListEqual(list(e.children), list(a.children))

        limit = 2
        with self.subTest(re=re, limit=limit):
            expected = expected[:limit]
            actual = [*Ito.from_re(re, s, limit=limit)]
            self.assertListEqual(expected, actual)
            for e, a in zip(expected, actual):
                self.assertListEqual(list(e.children), list(a.children))

    def test_from_match_complex(self):
        s = 'nine 9 ten 10 eleven 11 TWELVE 12 thirteen 13'
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)\s*)+')
        m = re.fullmatch(s)

        for exclude_keys in None, [1], ['phrase'], ['char', 'digit']:
            with self.subTest(exclude_keys=exclude_keys):
                if exclude_keys is None:
                    ito = Ito.from_match(m)
                else:
                    ito = Ito.from_match(m, *exclude_keys)

                itos = [ito, *ito.walk_descendants()]

                if exclude_keys is not None:
                    for k in exclude_keys:
                        if k == 0:
                            self.assertIn('0', [i.desc for i in itos])
                        else:
                            self.assertNotIn(k, [i.desc for i in itos])

                for i in itos:
                    k = i.desc
                    if i.desc.isnumeric():
                        k = int(k)
                    for span in m.spans(k):
                        j = s[slice(*span)]
                        self.assertIn(j, [str(i) for i in itos if i.desc == str(k)])

    def test_from_spans_simple(self):
        s = 'abcd' * 100
        spans = [*RandSpans(Span(1, 10), Span(0, 3)).generate(s)]
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                for i in _class.from_spans(s, *spans, desc=desc):
                    self.assertIsInstance(i, _class)
                    self.assertIs(s, i.string)
                    self.assertIn(i.span, spans)
                    self.assertEqual(desc, i.desc)
                    
    def test_from_spans_complex(self):
        s = 'abcd' * 100
        spans = [Span(20, 50), Span(0, 25), Span(50, 75)]  # Overlapping and unordered
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                expected = [_class(s, *span, desc) for span in spans]
                actual = [*_class.from_spans(s, *spans, desc=desc)]
                self.assertListEqual(expected, actual)
                    
    def test_from_spans_ito(self):
        s = ' abc '
        src = Ito(s, 1, -1)
        spans = [Span(1, 3), Span(0, 2)]  # Overlapping and unordered
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                expected = [_class(src, *span, desc) for span in spans]
                actual = [*_class.from_spans(src, *spans, desc=desc)]
                self.assertListEqual(expected, actual)

    def test_from_gaps_simple(self):
        s = 'abcd' * 10
        gaps = [*RandSpans(Span(1, 8), Span(0, 3)).generate(s)]
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                for i in _class.from_gaps(s, *gaps, desc=desc):
                    self.assertIsInstance(i, _class)
                    self.assertIs(s, i.string)
                    self.assertFalse(any(gap.start <= i.start <= i.stop <= gap.stop for gap in gaps))
                    self.assertEqual(desc, i.desc)
                    
    def test_from_gaps_complex(self):
        s = 'abcd' * 10
        gaps = [Span(10, 20), Span(5, 10), Span(20, 25)]  # Overlapping and unordered
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                expected = [
                    _class(s, 0, min(gap.start for gap in gaps), desc),
                    _class(s, max(gap.stop for gap in gaps), desc=desc)
                ]
                actual = [*_class.from_gaps(s, *gaps, desc=desc)]
                self.assertListEqual(expected, actual)
                    
    def test_from_gaps_ito(self):
        s = ' abc '
        src = Ito(s, 1, -1)
        gaps = [Span(1, 2), Span(0, 1)]  # Overlapping and unordered
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                expected = [_class(src, 2, desc=desc)]
                actual = [*_class.from_gaps(src, *gaps, desc=desc)]
                self.assertListEqual(expected, actual)
                    
    def test_from_substrings(self):
        string = 'abcd' * 10
        string = f' {string} '

        with self.subTest(spacing='Consecutive'):
            for size in ((1, 1), (2, 2), (1, 3), (2, 3)):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(0, 0))
                    subs = [*rs.generate(string, 1, -1)]
                    itos = Ito.from_substrings(string, subs)
                    self.assertListEqual(subs, [str(i) for i in itos])

        with self.subTest(spacing='Gaps'):
            for size in ((1, 1), (2, 2), (1, 3), (2, 3)):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(1, 2))
                    subs = [*rs.generate(string, 1, -1)]
                    itos = Ito.from_substrings(string, subs)
                    self.assertListEqual(subs, [str(i) for i in itos])

        with self.subTest(spacing='Overlaps'):
            for size in ((3, 3),):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(-1, -1))
                    subs = [*rs.generate(string, 1, -1)]
                    with self.assertRaises(Exception):
                        itos = [*Ito.from_substrings(string, subs)]

    def test_clone_basic(self):
        string = 'abc'
        d = 'x'
        ito = Ito(string, 1, 2, desc=d)

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
                'desc': 'z'
            }
        ]

        for pdict in params:
            with self.subTest(**pdict):
                expected = Ito(
                    string,
                    pdict.get('start', ito.start),
                    pdict.get('stop', ito.stop),
                    pdict.get('desc', ito.desc),
                )
                clone = ito.clone(**pdict)
                self.assertEqual(expected, clone)

    def test_clone_typing(self):
        s = '123'
        parent = IntIto(s, desc='parent')
        self.assertEqual('IntIto', type(parent).__name__)
        self.add_chars_as_children(parent, 'child')
        self.assertTrue(all(type(c).__name__ == 'IntIto' for c in parent.children))

        clone = parent.clone()
        self.assertEqual(len(parent.children), len(clone.children))
        for c, cc in zip(parent.children, clone.children):
            self.assertIsNot(c, cc)
            self.assertEqual(c, cc)

    def test_clone_children(self):
        s = 'abc'
        parent = Ito(s, desc='parent')
        self.add_chars_as_children(parent, 'child')

        for cc in (True, False):
            with self.subTest(clone_children=cc):
                clone = parent.clone(clone_children=cc)
                if cc:
                    self.assertSequenceEqual([*parent.children], [*clone.children])
                else:
                    self.assertEqual(0, len(clone.children))

    def test_clone_with_value_func(self):
        string = ' abcdef '
        f1 = lambda ito: str(ito).strip()
        f2 = lambda ito: str(ito).upper()

        root = Ito(string)
        self.assertEqual(string, root.value())

        clone = root.clone()
        self.assertEqual(string, clone.value())

        root.value_func = f1
        self.assertEqual(f1(root), root.value())
        self.assertEqual(string, clone.value())  # Ensure clone didn't change

        clone.value_func = f2
        self.assertEqual(f2(clone), clone.value())
        self.assertEqual(f1(root), root.value())  # Ensure root didn't change

        root.value_func = None
        self.assertEqual(string, root.value())
        self.assertEqual(f2(clone), clone.value())  # Ensure clone didn't change
