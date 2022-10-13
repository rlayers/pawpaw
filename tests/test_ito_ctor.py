import itertools

import regex
from segments import Ito, Span
from tests.util import _TestIto, RandSpans, RandSubstrings


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
                self.assertEqual(src, i[:])
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
                    self.assertEqual(s[start:stop], i[:])
                    
    def test_ctor_str_ito(self):
        for s in '', ' ', 'a', 'abc', ' abc ':
            for i in None, 0, 1:
                for j in -1, len(s), None:
                    src = Ito(s, i, j)
                    for start, stop in (None, None), (1, None), (None, -1), (1, -1):
                        with self.subTest(src=src, start=start, stop=stop):
                            ito = Ito(src, start, stop)
                            self.assertEqual(src.string, ito.string)
                            self.assertEqual(src[start:stop], ito[:])

    def test_from_match_simple(self):
        first = 'John'
        last = 'Doe'
        string = ' '.join((first, last))
        re = regex.compile(r'(?P<fn>.+)\s(?P<ln>.+)')
        m = re.fullmatch(string)

        desc = 'x'
        with self.subTest(group='Absent'):
            ito = Ito.from_match(m, desc=desc)
            self.assertEqual(m.group(), ito.__str__())
            self.assertEqual(desc, ito.desc)

        for group in 0, 1, 'fn', 2, 'ln':
            with self.subTest(group=group):
                ito = Ito.from_match(m, group, desc=desc)
                self.assertEqual(m.group(group), ito.__str__())
                self.assertEqual(desc, ito.desc)

    def test_from_re_str(self):
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)(?: |$))+')
        s = 'nine 9 ten 10 eleven 11 twelve 12 thirteen 13'

        root = Ito(s, desc='root')
        rv = [*Ito.from_re(re, s)]
        root.children.add(*rv)
        self.assertEqual(5, len(root.children))
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.desc == k] for k, val in itertools.groupby(itos, lambda x: x.desc)}
        self.assertEqual(5, len(grouped['word']))
        self.assertEqual(5, len(grouped['number']))
        self.assertEqual(9, len(grouped['digit']))

    def test_from_re_ito(self):
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)(?: |$))+')
        s = 'nine 9 ten 10 eleven 11 twelve 12 thirteen 13'

        root = Ito(s, s.index('ten'), s.index('thirteen'), desc='root')
        rv = [*Ito.from_re(re, root)]
        root.children.add(*rv)
        self.assertEqual(3, len(root.children))
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.desc == k] for k, val in itertools.groupby(itos, lambda x: x.desc)}
        self.assertEqual(3, len(grouped['word']))
        self.assertEqual(3, len(grouped['number']))
        self.assertEqual(6, len(grouped['digit']))
        
    def test_from_spans(self):
        s = 'abcd' * 100
        spans = [*RandSpans(Span(1, 10), Span(0, 3)).generate(s)]
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', self.IntIto)):
            with self.subTest(_class=cls_name):
                for i in _class.from_spans(s, *spans, desc=desc):
                    self.assertIsInstance(i, _class)
                    self.assertIs(s, i.string)
                    self.assertIn(i.span, spans)
                    self.assertEqual(desc, i.desc)

    def test_from_substrings(self):
        string = 'abcd' * 10
        string = f' {string} '

        with self.subTest(spacing='Consecutive'):
            for size in ((1, 1), (2, 2), (1, 3), (2, 3)):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(0, 0))
                    subs = [*rs.generate(string, 1, -1)]
                    itos = Ito.from_substrings(string, *subs)
                    self.assertListEqual(subs, [i.__str__() for i in itos])

        with self.subTest(spacing='Gaps'):
            for size in ((1, 1), (2, 2), (1, 3), (2, 3)):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(1, 2))
                    subs = [*rs.generate(string, 1, -1)]
                    itos = Ito.from_substrings(string, *subs)
                    self.assertListEqual(subs, [i.__str__() for i in itos])

        with self.subTest(spacing='Overlaps'):
            for size in ((3, 3),):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(-1, -1))
                    subs = [*rs.generate(string, 1, -1)]
                    with self.assertRaises(Exception):
                        itos = [*Ito.from_substrings(string, *subs)]

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
        parent = self.IntIto(s, desc='parent')
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
        f1 = lambda ito: ito[:].strip()
        f2 = lambda ito: ito[:].upper()

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
