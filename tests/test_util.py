import segments
import typing
from tests.util import _TestIto


class TestUtil(_TestIto):
    def test_find_unescaped_chars_invalid(self):
        s = ' abc '
        for src in s, segments.Ito(s, 1, -1):
          for char in [None, '', 'ab']
            with self.subTest(src=src, char=char):
                with self.assertRaises((TypeError, ValueError)):
                    i = next(segments.find_unescaped_chars(src, char))

        char = 'a'
        for src in s, segments.Ito(s, 1, -1):
          for escape in [None, '', 'ab']
            with self.subTest(src=src, char=char, escape=escape):
                with self.assertRaises((TypeError, ValueError)):
                    i = next(segments.find_unescaped_chars(src, char, escape))

    def test_find_unescaped_chars_trailing_escape(self):
        char = 'a'
        src = 'a\\'
        with self.subTest(src=src, char=char):
            with self.assertRaises(ValueError):
                rv = [*segments.find_unescaped_chars(src, char))
                
    def test_find_unescaped_chars_empty_src(self):
        s = ''
        char = 'a'
        for src in s, segments.Ito(s), segments.Ito('ab', 1, -1):
            with self.subTest(src=src, char=char):
                i = next(segments.find_unescaped_chars(src, char), None)
                self.assertIsNone(i)

    def test_find_unescaped_chars_not_present(self):
        s = ' abc '
        char = 'z'
        for src in s, segments.Ito(s, 1, -1):
            with self.subTest(src=src, char=char):
                i = next(segments.find_unescaped_chars(src, char), None)
                self.assertIsNone(i)

    def test_find_unescaped_chars_not_simple(self):
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
                    actual = [*segments.find_unescaped_chars(s, char)]
                    self.assertListEqual(expected, actual)
    
    def test_find_unescaped_chars_complex(self):
        s = ' a&b&&c '
        for src in s, segments.Ito(s, 1, -1):
            escape = '&'
            for char in 'a', 'b', 'c'
            with self.subTest(src=src, char=char, escape=escape):
                if char in ('a', 'c):
                    expected = [src[:].find(char)]
                else:
                    expected = []
                actual = [*segments.find_unescaped_chars(s, char, escape)]
                self.assertListEqual(expected, actual)
