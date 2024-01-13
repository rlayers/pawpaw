import regex

from pawpaw import Ito
from tests.util import _TestIto


class TestItoUtilityMethods(_TestIto):

    def test_to_line_str_col_empty(self):
        s = 'a\nb\nc'
        line = 1
        col = 0
        for i in range(0, len(s)):
            col += 1
            ito = Ito(s, i, i + 1)
            with self.subTest(string=s, ito=ito.span):
                expected = line, col
                actual = ito.to_line_col('\n')
                self.assertEqual(expected, actual)
                if s[i] == '\n':
                    line += 1
                    col = 0

    def test_to_line_str_non_empty(self):
        s = 'a\r\nb\r\nc'
        line = 1
        col = 0
        for i in range(0, len(s) - 1):
            col += 1
            ito = Ito(s, i, i + 2)
            with self.subTest(string=s, ito=ito.span):
                expected = line, col
                actual = ito.to_line_col('\r\n')
                self.assertEqual(expected, actual)
                if s[i] == '\n':
                    line += 1
                    col = 0

    def test_to_line_regex_non_empty(self):
        string = 'abc\r\ndef\nghi'
        eol = regex.compile(r'\r?\n', regex.DOTALL)
        matches = eol.findall(string)
        for i, ito in enumerate(Ito.from_gaps(string, Ito.from_re(eol, string)), 1):
            for sub in ito:
                with self.subTest(ito=sub):
                    expected = i, 1 + sub.start - ito.start
                    self.assertEqual(expected, sub.to_line_col(eol))
