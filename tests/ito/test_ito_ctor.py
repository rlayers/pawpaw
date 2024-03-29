import regex
from pawpaw import GroupKeys, Ito, Span
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

    def test_from_match_simple(self):
        first = 'John'
        last = 'Doe'
        string = ' '.join((first, last))
        re = regex.compile(r'(?P<fn>.+)\s(?P<ln>.+)')
        m = re.fullmatch(string)

        for group_keys in [1], ['fn'], [2], ['ln'], ['fn', 2], [1, 'ln']:
            with self.subTest(group_keys=group_keys):
                itos = Ito.from_match(m, group_keys=group_keys)
                for i in itos:
                    k = i.desc
                    if i.desc.isnumeric():
                        k = int(k)
                    self.assertEqual(m.group(k), str(i))

    def test_from_match_complex(self):
        s = 'nine 9 ten 10 eleven 11 TWELVE 12 thirteen 13'
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)\s*)+')
        m = re.fullmatch(s)

        for group_keys in GroupKeys.preferred(re), [1], ['phrase'], ['phrase', 'word', 'number'], ['char', 'digit']:
            with self.subTest(group_keys=group_keys):
                itos = Ito.from_match(m, group_keys=group_keys)
                for ito in itos:
                    branch = [ito]
                    branch.extend(ito.walk_descendants())
                    for i in branch:
                        self.assertTrue(any(i.desc == str(gk) for gk in group_keys))

    def test_from_re(self):
        s = 'the quick brown fox'

        re = 1
        with self.subTest(re=re):
            with self.assertRaises(TypeError):
                [*Ito.from_re(re, s)]

        group_filter = lambda m, gk: isinstance(gk, str)
        for re in [(pat := r'(?<word>\w+)'), regex.compile(pat)]:
            with self.subTest(re=re, group_filter=group_filter):
                expected = [*Ito.from_substrings(s, *s.split(), desc='word')]
                actual = [*Ito.from_re(re, s, group_filter)]
                self.assertListEqual(expected, actual)

        re = r'(?<phrase>(?:(?<word>(?<char>\w)+)(?:$|\s+))+)'
        with self.subTest(re=re):
            expected = [Ito(s, desc='0')]
            actual = [*Ito.from_re(re, s, group_filter=lambda m, gk: True)]
            self.assertListEqual(expected, actual)

        
        with self.subTest(re=re, group_filter=group_filter):
            expected = [Ito(s, desc='phrase')]
            actual = [*Ito.from_re(re, s, group_filter)]
            self.assertListEqual(expected, actual)
            
            expected = [*Ito.from_substrings(s, *s.split(), desc='word')]
            self.assertSequenceEqual(expected, actual[0].children)

            for child in actual[0].children:
                self.assertSequenceEqual([Ito(i, desc='char') for i in child], child.children)

        group_filter = lambda m, gk: gk in ['word', 'char']
        with self.subTest(re=re, group_filter=group_filter):
            actual = [*Ito.from_re(re, s, group_filter)]
            self.assertListEqual(expected, actual)

        for limit in -1, 0, 1, 2:
            with self.subTest(re=re, group_filter=group_filter, limit=limit):
                actual = [*Ito.from_re(re, s, group_filter, limit=limit)]
                self.assertEqual(max(limit, 0), len(actual))

        group_filter = lambda m, gk: gk in ['word']
        with self.subTest(re=re, group_filter=group_filter):
            actual = [*Ito.from_re(re, s, group_filter)]
            self.assertListEqual(expected, actual)

            self.assertTrue(all(len(i.children) == 0 for i in actual))

        group_filter = [2]
        with self.subTest(re=re, group_filter=group_filter):
            expected = [i.clone(desc='2') for i in expected]
            actual = [*Ito.from_re(re, s, group_filter)]
            self.assertListEqual(expected, actual)
            self.assertTrue(all(len(i.children) == 0 for i in actual))

        desc = 'other'
        with self.subTest(re=re, desc=desc):
            expected = [Ito(s, desc=desc)]
            actual = [*Ito.from_re(re, s, desc=desc)]
            self.assertListEqual(expected, actual)

    def test_from_spans_simple(self):
        s = 'abcd' * 100
        spans = [*RandSpans(Span(1, 10), Span(0, 3)).generate(s)]
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                for i in _class.from_spans(s, spans, desc=desc):
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
                actual = [*_class.from_spans(s, spans, desc=desc)]
                self.assertListEqual(expected, actual)
                    
    def test_from_spans_ito(self):
        s = ' abc '
        src = Ito(s, 1, -1)
        spans = [Span(1, 3), Span(0, 2)]  # Overlapping and unordered
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                expected = [_class(src, *span, desc) for span in spans]
                actual = [*_class.from_spans(src, spans, desc=desc)]
                self.assertListEqual(expected, actual)

    def test_from_gaps_src_str_1(self):
        desc = 'non gap'
        for s in '', 'a', ' ', 'ab', ' ab', 'a b', 'ab ', ' a b ':
            non_gaps = list[Ito]()
            expected = list[Ito]()
            for i in Ito(s):
                if i.str_isspace():
                    expected.append(i.clone(desc=desc))
                else:
                    non_gaps.append(i)

            for ngs in non_gaps, [ng.span for ng in non_gaps]:
                with self.subTest(src=s, non_gaps=ngs):
                    actual = [*Ito.from_gaps(s, ngs, desc)]
                    self.assertSequenceEqual(expected, actual)

    def test_from_gaps_src_ito_1(self):
        desc = 'non gap'
        for s in '', 'a', ' ', 'ab', ' ab', 'a b', 'ab ', ' a b ':
            s = f' {s} '
            src = Ito(s, 1, -1)
            non_gaps = list[Ito]()
            expected = list[Ito]()
            for i in src:
                if i.str_isspace():
                    expected.append(i.clone(desc=desc))
                else:
                    non_gaps.append(i)

            for ngs in non_gaps, [ng.span.offset(-1) for ng in non_gaps]:
                with self.subTest(src=src, non_gaps=ngs):
                    actual = [*Ito.from_gaps(src, ngs, desc)]
                    self.assertSequenceEqual(expected, actual)

    def test_from_gaps_src_str_2(self):
        src = ' abc '
        non_gap_starts = src.find('a'), src.find('c')

        for width in 0, 1:
            for ngt in 'Span', 'Ito':
                if ngt == 'Span':
                    non_gaps = [Span(s, s + width) for s in non_gap_starts]
                elif ngt == 'Ito':
                    non_gaps = [Ito(src, s, s + width) for s in non_gap_starts]
                for return_zero_widths in True, False:
                    with self.subTest(src=src, non_gap_width=width, non_gap_type=ngt, return_zero_widths=return_zero_widths):
                        expected = list[Ito]()
                        expected.append(Ito(src, stop=non_gaps[0].start))
                        expected.append(Ito(src, non_gaps[0].stop, non_gaps[-1].start))
                        expected.append(Ito(src, non_gaps[-1].stop))
                        if not return_zero_widths:
                            expected = [e for e in expected if len(e) > 0]
                        actual = [*Ito.from_gaps(src, non_gaps)]
                        self.assertListEqual(expected, actual)

    def test_from_gaps_src_ito_2(self):
        string = ' abc '
        src = Ito(string, 1, -1)
        non_gap_starts = src.str_find('a'), src.str_find('c')  # relative to src, not string

        for width in 0, 1:
            for ngt in 'Span', 'Ito':
                if ngt == 'Span':
                    non_gaps = [Span(s, s + width) for s in non_gap_starts]
                    offset = 0
                elif ngt == 'Ito':
                    non_gaps = [Ito(src, s, s + width) for s in non_gap_starts]
                    offset = -src.start
                for return_zero_widths in True, False:
                    with self.subTest(src=src, non_gap_width=width, non_gap_type=ngt, return_zero_widths=return_zero_widths):
                        expected = list[Ito]()
                        expected.append(Ito(src, non_gaps[0].stop + offset, non_gaps[-1].start + offset))
                        expected.append(Ito(src, non_gaps[-1].stop + offset, src.stop + offset))
                        if len(expected[-1]) == 0:
                            expected.pop(-1)
                        if not return_zero_widths:
                            expected = [e for e in expected if len(e) > 0]
                        actual = [*Ito.from_gaps(src, non_gaps)]
                        self.assertListEqual(expected, actual)

    def test_from_gaps_none(self):
        src = 'abc'
        desc = 'X'
        expected = Ito(src, desc=desc)
        actual = next(Ito.from_gaps(src, [], desc), None)
        self.assertIsNotNone(actual)
        self.assertEqual(expected, actual)

    def test_from_gaps_identity(self):
        src = 'abc'
        desc = 'X'
        actual = next(Ito.from_gaps(src, [Ito(src)], desc), None)
        self.assertIsNone(actual)

    def test_from_gaps_contiguous_non_gaps(self):
        src = 'abc'
        desc = 'X'
        actual = next(Ito.from_gaps(src, Ito(src), desc), None)
        self.assertIsNone(actual)            

    def test_from_gaps_with_zero_widths(self):
        desc = 'non gap'

        with self.subTest(non_gap_count=2, non_gap_proximity='adjacent', non_gap_extent='contained'):
            s = ' abc '
            root = Ito(s, 1, -1)
            root.children.add(*root)
            expected = [Ito(root, i, i, desc) for i in range(1, len(root))]
            rv = [*root.from_gaps(root, root.children, desc, True)]
            self.assertEqual(len(expected), len(rv))
            self.assertSequenceEqual(expected, rv)

        with self.subTest(non_gap_count=2, non_gap_proximity='overlapping', non_gap_extent='contained'):
            overlapping_non_gaps = [Ito(s, *root.span), Ito(s, root.start + 1, root.stop)]
            rv = [*root.from_gaps(root, overlapping_non_gaps, desc, True)]
            self.assertEqual(0, len(rv))

        with self.subTest(non_gap_count=3, non_gap_proximity='overlapping', non_gap_extent='contained'):
            overlapping_non_gaps = [Ito(s, root.start + i, root.stop) for i in range(0, len(root))]
            rv = [*root.from_gaps(root, overlapping_non_gaps, desc, True)]
            self.assertEqual(0, len(rv))

        with self.subTest(non_gap_count=2, non_gap_proximity='overlapping', non_gap_extent='non-contained'):
            overlapping_non_gaps = [Ito(s, 0, len(s) - 1), Ito(s, 1, len(s) + 2)]
            rv = [*root.from_gaps(root, overlapping_non_gaps, desc, True)]
            self.assertEqual(0, len(rv))

        with self.subTest(non_gap_count=1, non_gap_proximity='N/A', non_gap_extent='non-contained', location='prior'):
            ng_prior = [Ito(s, 0, 1)]
            rv = [*root.from_gaps(root, ng_prior, return_zero_widths=True, desc=desc)]
            self.assertEqual(1, len(rv))
            self.assertEqual(root.clone(desc=desc), rv[0])

        with self.subTest(non_gap_count=1, non_gap_proximity='N/A', non_gap_extent='non-contained', location='after'):
            ng_after = [Ito(s, -1)]
            rv = [*root.from_gaps(root, ng_after, desc, True)]
            self.assertEqual(1, len(rv))
            self.assertEqual(root.clone(desc=desc), rv[0])

        with self.subTest(non_gap_count=2, non_gap_proximity='overlapping', non_gap_extent='non-contained'):
            ng = ng_prior + ng_after
            rv = [*root.from_gaps(root, ng, desc, True)]
            self.assertEqual(1, len(rv))
            self.assertEqual(root.clone(desc=desc), rv[0])

    def test_from_gaps_simple(self):
        s = 'abcd' * 10
        non_gaps = [*RandSpans(Span(1, 8), Span(0, 3)).generate(s)]
        desc = 'x'
        for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
            with self.subTest(_class=cls_name):
                for i in _class.from_gaps(s, non_gaps, desc):
                    self.assertIsInstance(i, _class)
                    self.assertIs(s, i.string)
                    self.assertFalse(any(gap.start <= i.start <= i.stop <= gap.stop for gap in non_gaps))
                    self.assertEqual(desc, i.desc)

    def test_from_gaps_complex(self):
        s = 'abcd' * 10
        non_gaps = [Span(10, 20), Span(5, 10), Span(20, 25)]  # Overlapping and unordered
        desc = 'x'
        for ordered in True, False:
            for cls_name, _class in (('Base (Ito)', Ito), ('Derived (IntIto)', IntIto)):
                with self.subTest(_class=cls_name, ordered=ordered):
                    if ordered:
                        ngs = non_gaps.copy()
                        ngs.sort(key=lambda i: i.start)
                        expected = [
                            _class(s, 0, min(gap.start for gap in non_gaps), desc),
                            _class(s, max(gap.stop for gap in non_gaps), desc=desc)
                        ]
                        actual = [*_class.from_gaps(s, ngs, desc)]
                        self.assertListEqual(expected, actual)
                    else:
                        ngs = non_gaps.copy()
                        with self.assertRaises(ValueError):
                            [*_class.from_gaps(s, ngs, desc)]

    def test_from_substrings(self):
        string = 'abcd' * 10
        string = f' {string} '

        with self.subTest(spacing='Consecutive'):
            for size in ((1, 1), (2, 2), (1, 3), (2, 3)):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(0, 0))
                    subs = [*rs.generate(string, 1, -1)]
                    itos = Ito.from_substrings(string, *subs)
                    self.assertListEqual(subs, [str(i) for i in itos])

        with self.subTest(spacing='Gaps'):
            for size in ((1, 1), (2, 2), (1, 3), (2, 3)):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(1, 2))
                    subs = [*rs.generate(string, 1, -1)]
                    itos = Ito.from_substrings(string, *subs)
                    self.assertListEqual(subs, [str(i) for i in itos])

        with self.subTest(spacing='Overlaps'):
            for size in ((3, 3),):
                with self.subTest(size_range=size):
                    rs = RandSubstrings(size, Span(-1, -1))
                    subs = [*rs.generate(string, 1, -1)]
                    with self.assertRaises(Exception):
                        [*Ito.from_substrings(string, *subs)]

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
        s = ' one two three '
        root = Ito(s, 1, -1, 'root')
        root.children.add(*root.str_split())
        for c in root.children:
            c.children.add(*c)

        self.assertEqual(len(s.split()), len(root.children))
        for c in root.children:
            self.assertEqual(len(c), len(c.children))

        clone = root.clone()
        self.assertSequenceEqual([*root.children], [*clone.children])
        for rc, cc in zip(root.children, clone.children):
            self.assertSequenceEqual([*rc.children], [*cc.children])

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
