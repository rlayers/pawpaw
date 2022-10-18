import segments

from tests.util import _TestIto


class TestFindUnescaped(_TestIto):
    def test_find_unescaped_invalid(self):
        s = ' abc '
        for src in s, segments.Ito(s, 1, -1):
            for char in [None, '', 'ab']:
                with self.subTest(src=src, char=char):
                    with self.assertRaises((TypeError, ValueError)):
                        next(segments.find_unescaped(src, char))

        char = 'a'
        for src in s, segments.Ito(s, 1, -1):
            for escape in [None, '', '\\\\']:
                with self.subTest(src=src, char=char, escape=escape):
                    with self.assertRaises((TypeError, ValueError)):
                        next(segments.find_unescaped(src, char, escape))

    def test_find_unescaped_trailing_escape(self):
        char = 'a'
        src = 'a\\'
        with self.subTest(src=src, char=char):
            with self.assertRaises(ValueError):
                [*segments.find_unescaped(src, char)]
                
    def test_find_unescaped_empty_src(self):
        s = ''
        char = 'a'
        for src in s, segments.Ito(s), segments.Ito('ab', 1, -1):
            with self.subTest(src=src, char=char):
                i = next(segments.find_unescaped(src, char), None)
                self.assertIsNone(i)

    def test_find_unescaped_not_present(self):
        s = ' abc '
        char = 'z'
        for src in s, segments.Ito(s), segments.Ito(s, 1, -1):
            with self.subTest(src=src, char=char):
                i = next(segments.find_unescaped(src, char), None)
                self.assertIsNone(i)

    def test_find_unescaped_simple(self):
        for string in 'a', 'b':
            char = 'a'
            for pre in range(1, 5):
                s = '\\' * pre + string
                with self.subTest(src=s, char=char):
                    if pre & 1:  # odd
                        expected = []
                    else:        # even
                        expected = s.find(char)
                        expected = [] if expected == -1 else [expected]
                    actual = [*segments.find_unescaped(s, char)]
                    self.assertListEqual(expected, actual)
    
    def test_find_unescaped_complex(self):
        s = ' a&b&&c '
        escape = '&'
        for src in s, segments.Ito(s, 1, -1):
            for char in 'a', 'b', 'c':
                with self.subTest(src=src, char=char, escape=escape):
                    if char == 'b':
                        expected = []
                    else:
                        expected = [src.__str__().find(char)]
                    actual = [*segments.find_unescaped(src, char, escape)]
                    self.assertListEqual(expected, actual)


class TestSplitUnescaped(_TestIto):
    def test_split_unescaped_complex(self):
        s = ' a&b&&c '
        escape = '&'
        for src in s, segments.Ito(s, 1, -1):
            for char in 'a', 'b', 'c':
                with self.subTest(src=src, char=char, escape=escape):
                    if char == 'b':
                        expected = [src]
                    else:
                        i = src.__str__().index(char)
                        expected = [src[:i], src[i + 1:]]
                actual = [*segments.split_unescaped(src, char, escape)]
                self.assertListEqual(expected, actual)

    def test_split_unescaped_prefix_suffix(self):
        s = 'aba'
        for src in s, segments.Ito(s):
            for char in 'a', 'b', 'c':
                with self.subTest(src=src, char=char):
                    if isinstance(src, str):
                        expected = src.split(char)
                    elif char == 'a':
                        expected = [src[0:0], src[1:1+1], src[3:3]]
                    elif char == 'b':
                        expected = [src[0:1], src[2:3]]
                    else:  # char == 'c'
                        expected = [src]
                    actual = [*segments.split_unescaped(src, char)]
                    self.assertListEqual(expected, actual)
