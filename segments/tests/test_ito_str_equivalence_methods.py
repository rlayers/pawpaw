from unittest import TestCase

from segments import Ito
from segments.tests.util import _TestIto


class TestItoStrEquivalenceMethods(_TestIto):

    def test_str_count(self):
        s = 'ab' * 10
        i = Ito(s, 2, -2)
        self.assertEqual(s.count('ab', 2, -2), i.str_count('ab'))
        self.assertEqual(s.count('ab', 4, -4), i.str_count('ab', 2, -2))

    def test_str_endswith(self):
        string = f' {"abc" * 2} '
        ito = Ito(string, 1, -1)

        sep = None
        with self.subTest(sep=sep):
            with self.assertRaises(TypeError):
                ito.str_startswith(sep)

        for sep in ['', 'a', 'b', 'ab', 'bc', 'c', 'abc', 'z']:
            with self.subTest(sep=sep):
                for start in [-100, -1, None, 0, 1, 100]:
                    with self.subTest(start=start):
                        for end in [-100, -1, None, 0, 1, 100]:
                            with self.subTest(end=end):
                                expected = string.strip().endswith(sep, start, end)
                                actual = ito.str_endswith(sep, start, end)
                                self.assertEqual(expected, actual)

    def test_str_find(self):
        s = 'abcdefgh'
        i = Ito(s, 2, -2)
        self.assertEqual(s.find('ab', 2, -2), i.str_find('ab'))
        self.assertEqual(s.find('cd', 2, -2), i.str_find('cd'))
        self.assertEqual(s.find('cd', 3, -3), i.str_find('cd', 1, -1))
        self.assertEqual(s.find('de', 3, -3), i.str_find('de', 1, -1))

    def test_str_index(self):
        s = 'abcdefgh'
        i = Ito(s, 2, -2)
        with self.assertRaises(ValueError):
            i.str_index('ab')
        self.assertEqual(s.find('cd', 2, -2), i.str_index('cd'))
        with self.assertRaises(ValueError):
            i.str_index('cd', 1, -1)
        self.assertEqual(s.find('de', 3, -3), i.str_index('de', 1, -1))

    #region 'is' methods

    def test_str_isalnum(self):
        for string in ('', 'abc', '123', 'abc123', '!@#', 'a!2#c'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isalnum(), ito.str_isalnum())

    def test_str_isalpha(self):
        for string in ('', 'abc', '123', 'abc123', '!@#', 'a!2#c'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isalpha(), ito.str_isalpha())

    def test_str_isascii(self):
        for string in ('', 'abc', '123', 'abc123', '!@#', 'a!2#c', '\uF609', 'a\uF609'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isalnum(), ito.str_isalnum())

    def test_str_isdecimal(self):
        for string in ('', 'abc', '123', 'abc123', '!@#', 'a!2#c'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isdecimal(), ito.str_isdecimal())

    def test_str_isdigit(self):
        for string in ('', 'abc', '123', 'abc123', '!@#', 'a!2#c', '¾'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isdigit(), ito.str_isdigit())

    def test_str_isidentifier(self):
        for string in ('', 'any', 'python', 'or and', 'and', 'not'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isidentifier(), ito.str_isidentifier())

    def test_str_islower(self):
        for string in ('', 'abc', 'abc123', 'AbC', 'AB', 'AB12', '123'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.islower(), ito.str_islower())

    def test_str_isnumeric(self):
        for string in ('', 'abc', '123', 'abc123', '!@#', 'a!2#c', '¾'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isnumeric(), ito.str_isnumeric())

    def test_str_isprintable(self):
        for string in ('', ' ', '\t', 'a b', '\t\n', '   '):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isprintable(), ito.str_isprintable())

    def test_str_isspace(self):
        for string in ('', ' ', '\t', 'a b', '\t\n', '   '):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isspace(), ito.str_isspace())

    def test_str_istitle(self):
        for string in ('', 'The', 'The Man in the Hat', 'a man', 'A MAN', 'A Man'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isidentifier(), ito.str_isidentifier())

    def test_str_isupper(self):
        for string in ('', 'abc', 'abc123', 'AbC', 'AB', 'AB12', '123'):
            with self.subTest(string=string):
                ito = Ito(string)
                self.assertEqual(string.isupper(), ito.str_isupper())

    #endregion

    def test_str_lstrip(self):
        self.assertTrue(False)

    def test_str_partition(self):
        string = f' abc '
        ito = Ito(string, 1, -1)

        for sep in [None, '']:
            with self.subTest(sep=sep):
                with self.assertRaises(ValueError):
                    ito.str_partition(sep)

        for sep in ['a', 'b', 'ab', 'bc', 'abc', 'z']:
            with self.subTest(sep=sep):
                expected = string.strip().partition(sep)
                actual = ito.str_partition(sep)
                self.assertEqual(type(expected), type(actual))
                expected = list(expected)
                actual = list(i.__str__() for i in actual)
                self.assertListEqual(expected, actual)

    def test_str_removeprefix(self):
        self.assertTrue(False)

    def test_str_removesuffix(self):
        self.assertTrue(False)

    def test_str_rfind(self):
        self.assertTrue(False)

    def test_str_rindex(self):
        self.assertTrue(False)
    def test_str_rpartition(self):
        self.assertTrue(False)

    def test_str_rsplit(self):
        self.assertTrue(False)

    def test_str_rstrip(self):
        self.assertTrue(False)

    def test_str_split(self):
        with self.subTest(sep=None):
            for s in ['', ' ', ' a', ' a', ' a ', ' a b', ' a b ', '\ta\nb\rc']:
                with self.subTest(string=s):
                    ito = Ito(s)
                    expected = [*Ito.from_substrings(s, *s.split())]
                    actual = ito.str_split()
                    self.assertEqual(len(expected), len(actual))
                    for e, a in zip(expected, actual):
                        self.assertEqual(e, a)

        s = f' {"abc" * 3} '
        ito = Ito(s, 1, -1)

        sep = ''
        with self.subTest(sep=sep, string=s):
            with self.assertRaises(ValueError):
                ito.str_split(sep)

        for sep in ['a', 'b', 'ab', 'bc', 'c', 'abc', 'z']:
            with self.subTest(sep=sep, string=s):
                expected = list(s for s in s.strip().split(sep))
                actual = list(i.__str__() for i in ito.str_split(sep))
                self.assertListEqual(expected, actual)

    def test_str_splitlines(self):
        self.assertTrue(False)

    def test_str_startswith(self):
        string = f' {"abc" * 2} '
        ito = Ito(string, 1, -1)

        sep = None
        with self.subTest(sep=sep):
            with self.assertRaises(TypeError):
                ito.str_startswith(sep)

        for sep in ['', 'a', 'b', 'ab', 'bc', 'c', 'abc', 'z']:
            with self.subTest(sep=sep):
                for start in [-100, -1, None, 0, 1, 100]:
                    with self.subTest(start=start):
                        for end in [-100, -1, None, 0, 1, 100]:
                            with self.subTest(end=end):
                                expected = string.strip().startswith(sep, start, end)
                                actual = ito.str_startswith(sep, start, end)
                                self.assertEqual(expected, actual)

    def test_str_strip(self):
        self.assertTrue(False)
