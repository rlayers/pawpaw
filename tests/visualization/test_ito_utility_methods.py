from pawpaw import Ito
from tests.util import _TestIto


class TestItoUtilityMethods(_TestIto):

    def test_to_line_col_empty(self):
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

    def test_to_line_non_empty(self):
        s = 'a\nb\nc'
        line = 1
        col = 0
        for i in range(0, len(s) - 1):
            col += 1
            ito = Ito(s, i, i + 2)
            with self.subTest(string=s, ito=ito.span):
                expected = line, col
                actual = ito.to_line_col('\n')
                self.assertEqual(expected, actual)
                if s[i] == '\n':
                    line += 1
                    col = 0
