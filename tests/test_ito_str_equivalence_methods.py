from segments import Ito
from tests.util import _TestIto


class TestItoStrEquivalenceMethods(_TestIto):

    def test_str_count(self):
        s = 'ab' * 10
        i = Ito(s, 2, -2)
        for sub in 'ab', 'ba':
            with self.subTest(sub=sub):
                self.assertEqual(str(i).count(sub), i.str_count(sub))
                self.assertEqual(str(i).count(sub, 2, -2), i.str_count(sub, 2, -2))
                self.assertEqual(str(i).count(sub, 3, -3), i.str_count(sub, 3, -3))
                self.assertEqual(str(i).count(sub, 4), i.str_count(sub, 4))
                self.assertEqual(str(i).count(sub, None, -4), i.str_count(sub, end=-4))

    def test_str_endswith(self):
        s = f' {"abc" * 2} '
        ito = Ito(s, 1, -1)

        sep = None
        with self.subTest(src=s, sep=sep):
            with self.assertRaises(TypeError):
                ito.str_startswith(sep)

        for sep in ['', 'a', 'b', 'ab', 'bc', 'c', 'abc', 'z']:
            for start in [-100, -1, None, 0, 1, 100]:
                for end in [-100, -1, None, 0, 1, 100]:
                    with self.subTest(src=s, sep=sep, start=start, end=end):
                        expected = s.strip().endswith(sep, start, end)
                        actual = ito.str_endswith(sep, start, end)
                        self.assertEqual(expected, actual)

    def test_str_find(self):
        s = 'abcdefgh' * 2
        i = Ito(s, 2, -2)
        self.assertEqual(s.find('ab', 2, -2), i.str_find('ab'))
        self.assertEqual(s.find('cd', 2, -2), i.str_find('cd'))
        self.assertEqual(s.find('cd', 3, -3), i.str_find('cd', 1, -1))
        self.assertEqual(s.find('de', 3, -3), i.str_find('de', 1, -1))

    def test_str_index(self):
        s = '12' + 'abcd' * 2 + '34'
        i = Ito(s, 2, -2)
        with self.assertRaises(ValueError):
            i.str_index('12')
        self.assertEqual(s.index('cd', 2, -2), i.str_index('cd'))
        with self.assertRaises(ValueError):
            i.str_index('ab', 1, 3)
        self.assertEqual(s.index('ab', 4), i.str_index('ab', 1))

    # region 'is' methods

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
        for s in '', 'abc', 'abc123', 'AbC', 'AB', 'AB12', '123':
            with self.subTest(string=s):
                ito = Ito(s)
                self.assertEqual(s.isupper(), ito.str_isupper())

    # endregion

    # region strip methods

    def test_str_lstrip(self):
        for s in '', 'abc', 'abc123', 'a1b2c3':
            for chars in None, '', 'a', 'ba', 'c', 'cb', 'x', 'ac', '32ba', '123abc':
                with self.subTest(string=s, chars=chars):
                    i = Ito(s)
                    self.assertEqual(s.lstrip(chars), str(i.str_lstrip(chars)))
                    
    def test_str_rstrip(self):
        for s in '', 'abc', 'abc123', 'a1b2c3':
            for chars in None, '', 'a', 'ba', 'c', 'cb', 'x', 'ac', '32ba', '123abc':
                with self.subTest(string=s, chars=chars):
                    i = Ito(s)
                    self.assertEqual(s.rstrip(chars), str(i.str_rstrip(chars)))

    def test_str_strip(self):
        for s in '', 'abc', 'abc123', 'a1b2c3':
            for chars in None, '', 'a', 'ba', 'c', 'cb', 'x', 'ac', '32ba', '123abc':
                with self.subTest(string=s, chars=chars):
                    i = Ito(s)
                    self.assertEqual(s.strip(chars), str(i.str_strip(chars)))

    # endregion

    # region partition and split methods
    
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
                actual = list(str(i) for i in actual)
                self.assertListEqual(expected, actual)

    def test_str_rpartition(self):
        string = f' abc '
        ito = Ito(string, 1, -1)

        for sep in [None, '']:
            with self.subTest(sep=sep):
                with self.assertRaises(ValueError):
                    ito.str_rpartition(sep)

        for sep in ['a', 'b', 'ab', 'bc', 'abc', 'z']:
            with self.subTest(sep=sep):
                expected = string.strip().rpartition(sep)
                actual = ito.str_rpartition(sep)
                self.assertEqual(type(expected), type(actual))
                expected = list(expected)
                actual = list(str(i) for i in actual)
                self.assertListEqual(expected, actual)

    def test_str_rsplit(self):
        for s in ['', ' ', ' a', ' a', ' a ', ' a b', ' a b ', '\ta\nb\rc']:
            for maxsplit in -1, 0, 1:
                with self.subTest(string=s, sep=None, maxsplit=maxsplit):
                    ito = Ito(s)
                    expected = [*Ito.from_substrings(s, *s.rsplit(maxsplit=maxsplit))]
                    actual = ito.str_rsplit(maxsplit=maxsplit)
                    self.assertListEqual(expected, actual)

        s = f' {"xyz" * 3} '
        ito = Ito(s, 1, -1)

        sep = ''
        with self.subTest(string=s, sep=sep):
            with self.assertRaises(ValueError):
                ito.str_rsplit(sep)

        for sep in ['x', 'y', 'xy', 'yz', 'z', 'xyz', 'z']:
            for maxsplit in -1, 0, 1:
                with self.subTest(string=s, sep=sep, maxsplit=maxsplit):
                    expected = list(s for s in s.strip().rsplit(sep, maxsplit))
                    actual = list(str(i) for i in ito.str_rsplit(sep, maxsplit))
                    self.assertListEqual(expected, actual)

    def test_str_split(self):
        for s in ['', ' ', ' a', ' a', ' a ', ' a b', ' a b ', '\ta\nb\rc', 'a b c d e']:
            for maxsplit in -1, 0, 1:
                with self.subTest(string=s, sep=None, maxsplit=maxsplit):
                    ito = Ito(s)
                    expected = [*Ito.from_substrings(s, *s.split(maxsplit=maxsplit))]
                    actual = ito.str_split(maxsplit=maxsplit)
                    self.assertListEqual(expected, actual)

        s = f' {"xyz" * 3} '
        ito = Ito(s, 1, -1)

        sep = ''
        with self.subTest(string=s, sep=sep):
            with self.assertRaises(ValueError):
                ito.str_split(sep)

        for sep in ['x', 'y', 'xy', 'yz', 'z', 'xyz', 'z']:
            for maxsplit in -1, 0, 1:
                with self.subTest(string=s, sep=sep, maxsplit=maxsplit):
                    expected = list(s for s in s.strip().split(sep, maxsplit))
                    actual = list(str(i) for i in ito.str_split(sep, maxsplit))
                    self.assertListEqual(expected, actual)

    def test_str_splitlines(self):
        basis = ''
        ito = Ito(basis)
        with self.subTest(string=basis, ito_span=ito.span, keepends=None):
            expected = basis.splitlines()
            actual = [str(i) for i in ito.str_splitlines()]
            self.assertListEqual(expected, actual)

        basis = '\n'
        ito = Ito(basis)
        with self.subTest(string=basis, ito_span=ito.span, keepends=None):
            expected = basis.splitlines()
            actual = [str(i) for i in ito.str_splitlines()]
            self.assertListEqual(expected, actual)

        basis = '__'
        ito = Ito(basis, 1, -1)
        with self.subTest(string=basis, ito_span=ito.span, keepends=None):
            expected = basis[slice(*ito.span)].splitlines()
            actual = [str(i) for i in ito.str_splitlines()]
            self.assertListEqual(expected, actual)

        basis = 'The\nquick\rbrown\r\nfox\vjumped\fover\xc1the\x1dlazy\u2028dogs.'
        paddings = ('', '\n', '\n\n', '\n\n\n', '\u2029', '\u2029\u2029')
        for prefix in paddings:
            for suffix in paddings:
                s = f'{prefix}{basis}{suffix}'
                ito = Ito(s, 1, -1)
                for keepends in True, False:
                    with self.subTest(string=s, ito_span=ito.span, keepends=keepends):
                        expected = s[1:-1].splitlines(keepends)
                        actual = [str(i) for i in ito.str_splitlines(keepends)]
                        self.assertListEqual(expected, actual)

    # endregion

    def test_str_removeprefix(self):
        s = '_abc_'
        i = Ito(s, 1, -1)
        self.assertEqual(s[1:-1].removeprefix('_'), str(i.str_removeprefix('_')))
        self.assertEqual(s[1:-1].removeprefix('a'), str(i.str_removeprefix('a')))

    def test_str_removesuffix(self):
        s = '_abc_'
        i = Ito(s, 1, -1)
        self.assertEqual(s[1:-1].removesuffix('_'), str(i.str_removesuffix('_')))
        self.assertEqual(s[1:-1].removesuffix('c'), str(i.str_removesuffix('c')))

    def test_str_rfind(self):
        s = 'abcdefgh' * 2
        i = Ito(s, 2, -2)
        self.assertEqual(s.rfind('ab', 2, -2), i.str_rfind('ab'))
        self.assertEqual(s.rfind('cd', 2, -2), i.str_rfind('cd'))
        self.assertEqual(s.rfind('cd', 3, -3), i.str_rfind('cd', 1, -1))
        self.assertEqual(s.rfind('de', 3, -3), i.str_rfind('de', 1, -1))

    def test_str_rindex(self):
        s = '12' + 'abcd' * 2 + '34'
        i = Ito(s, 2, -2)
        with self.assertRaises(ValueError):
            i.str_rindex('34')
        self.assertEqual(s.rindex('cd', 2, -2), i.str_rindex('cd'))
        with self.assertRaises(ValueError):
            i.str_rindex('cd', -5, -3)
        self.assertEqual(s.rindex('ab', 4), i.str_rindex('ab', 1))

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
