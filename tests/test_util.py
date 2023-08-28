import pawpaw

from tests.util import _TestIto


class TestFindUnescaped(_TestIto):
    def test_find_unescaped_invalid(self):
        s = ' abc '
        for src in s, pawpaw.Ito(s, 1, -1):
            for chars in [None, '']:
                with self.subTest(src=src, chars=chars):
                    with self.assertRaises((TypeError, ValueError)):
                        next(pawpaw.find_unescaped(src, chars))

        for chars in 'a', 'ab':
            for src in s, pawpaw.Ito(s, 1, -1):
                for escape in [None, '', '\\\\']:
                    with self.subTest(src=src, chars=chars, escape=escape):
                        with self.assertRaises((TypeError, ValueError)):
                            next(pawpaw.find_unescaped(src, chars, escape))

    def test_find_unescaped_trailing_escape(self):
        chars = 'a'
        src = 'a\\'
        with self.subTest(src=src, chars=chars):
            with self.assertRaises(ValueError):
                [*pawpaw.find_unescaped(src, chars)]
                
    def test_find_unescaped_empty_src(self):
        s = ''
        chars = 'a'
        for src in s, pawpaw.Ito(s), pawpaw.Ito('ab', 1, -1):
            with self.subTest(src=src, chars=chars):
                i = next(pawpaw.find_unescaped(src, chars), None)
                self.assertIsNone(i)

    def test_find_unescaped_not_present(self):
        s = ' abc '
        chars = 'z'
        for src in s, pawpaw.Ito(s), pawpaw.Ito(s, 1, -1):
            with self.subTest(src=src, chars=chars):
                i = next(pawpaw.find_unescaped(src, chars), None)
                self.assertIsNone(i)

    def test_find_unescaped_multiple(self):
        for string in 'a', 'b', 'ab', 'abc', 'bac':
            for chars in 'a', 'ab', 'cb':
                with self.subTest(src=string, chars=chars):
                    expected = [i for i, c in enumerate(string) if c in chars]
                    actual = [*pawpaw.find_unescaped(string, chars)]
                    self.assertListEqual(expected, actual)

    def test_find_unescaped_simple(self):
        for string in 'a', 'b':
            chars = 'a'
            for pre in range(1, 5):
                s = '\\' * pre + string
                with self.subTest(src=s, chars=chars):
                    if pre & 1:  # odd
                        expected = []
                    else:        # even
                        expected = s.find(chars)
                        expected = [] if expected == -1 else [expected]
                    actual = [*pawpaw.find_unescaped(s, chars)]
                    self.assertListEqual(expected, actual)
    
    def test_find_unescaped_complex(self):
        s = ' a&b&&c '
        escape = '&'
        for src in s, pawpaw.Ito(s, 1, -1):
            for chars in 'a', 'b', 'c':
                with self.subTest(src=src, chars=chars, escape=escape):
                    if chars == 'b':
                        expected = []
                    else:
                        expected = [str(src).find(chars)]
                    actual = [*pawpaw.find_unescaped(src, chars, escape)]
                    self.assertListEqual(expected, actual)


class TestSplitUnescaped(_TestIto):
    def test_split_unescaped_complex(self):
        s = ' a&b&&c '
        escape = '&'
        for src in s, pawpaw.Ito(s, 1, -1):
            for chars in 'a', 'b', 'c':
                with self.subTest(src=src, chars=chars, escape=escape):
                    if chars == 'b':
                        expected = [src]
                    else:
                        i = str(src).index(chars)
                        expected = [src[:i], src[i + 1:]]
                actual = [*pawpaw.split_unescaped(src, chars, escape)]
                self.assertListEqual(expected, actual)

    def test_split_unescaped_prefix_suffix(self):
        s = 'aba'
        for src in s, pawpaw.Ito(s):
            for chars in 'a', 'b', 'c':
                with self.subTest(src=src, chars=chars):
                    if isinstance(src, str):
                        expected = src.split(chars)
                    elif chars == 'a':
                        expected = [src[0:0], src[1:1+1], src[3:3]]
                    elif chars == 'b':
                        expected = [src[0:1], src[2:3]]
                    else:  # chars == 'c'
                        expected = [src]
                    actual = [*pawpaw.split_unescaped(src, chars)]
                    self.assertListEqual(expected, actual)


class TestFindBalanced(_TestIto):
    def test_find_balanced(self):
        lchar = '('
        rchar = ')'
        balanced_segments = [r'(\))', r'(\()', '()', '(a)', '(a(b))', '()', '(123(abc)(def)456)']

        for b in [*balanced_segments]:
            with self.subTest(src=b, lchar=lchar, rchar=rchar):
                actual = next(pawpaw.find_balanced(b, lchar, rchar))
                self.assertEqual(b, actual)

            b = pawpaw.Ito(b)
            lcito = pawpaw.Ito(lchar)
            rcito = pawpaw.Ito(rchar)
            with self.subTest(src=b, lchar=lcito, rchar=rcito):
                actual = next(pawpaw.find_balanced(b, lcito, rcito))
                self.assertEqual(b, actual)

            b = pawpaw.Ito(f'({b})')
            lcito = pawpaw.Ito(lchar)
            rcito = pawpaw.Ito(rchar)
            with self.subTest(src=b, lchar=lcito, rchar=rcito, start=1, stop=-1):
                actual = next(pawpaw.find_balanced(b, lcito, rcito, start=1, stop=-1))
                self.assertEqual(b[1:-1], actual)

        b = ''.join(balanced_segments)
        with self.subTest(src=b, lchar=lchar, rchar=rchar):
            actual = [*pawpaw.find_balanced(b, lchar, rchar)]
            self.assertListEqual(balanced_segments, actual)
