from pawpaw import Ito
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
        for ito in Ito(s), Ito(s, 2, -2):
            for find_indices in (None, None), (1, -1):
                for pat in 'ab', 'cd', 'de':
                    with self.subTest(string=s, ito=ito, pattern=pat, start=find_indices[0], stop=find_indices[1]):
                        expected = str(ito).find(pat, *find_indices)
                        self.assertEqual(expected, ito.str_find(pat, *find_indices))

    def test_str_index(self):
        s = ' 12' + 'abcd' * 2 + '34 '
        for ito in Ito(s), Ito(s, 1, -1):
            for find_indices in (None, None), (1, -1), (2, -2), (1, 3):
                for pat in '12', 'ab', 'cd', 'de':
                    with self.subTest(string=s, ito=ito, pattern=pat, start=find_indices[0], stop=find_indices[1]):
                        try:
                            expected = str(ito).index(pat, *find_indices)
                            actual = None
                        except ValueError:
                            with self.assertRaises(ValueError):
                                actual = ito.str_index(pat, *find_indices)

                        if actual is None:
                            actual = ito.str_index(pat, *find_indices)
                            self.assertEqual(expected, actual)

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
                    s_rv = s.lstrip(chars)
                    i_rv = i.str_lstrip(chars)
                    self.assertEqual(s is s_rv, i is i_rv)
                    self.assertEqual(s_rv, str(i_rv))
                    
    def test_str_rstrip(self):
        for s in '', 'abc', 'abc123', 'a1b2c3':
            for chars in None, '', 'a', 'ba', 'c', 'cb', 'x', 'ac', '32ba', '123abc':
                with self.subTest(string=s, chars=chars):
                    i = Ito(s)
                    s_rv = s.rstrip(chars)
                    i_rv = i.str_rstrip(chars)
                    self.assertEqual(s is s_rv, i is i_rv)
                    self.assertEqual(s_rv, str(i_rv))                    

    def test_str_strip(self):
        for s in '', 'abc', 'abc123', 'a1b2c3':
            for chars in None, '', 'a', 'ba', 'c', 'cb', 'x', 'ac', '32ba', '123abc':
                with self.subTest(string=s, chars=chars):
                    i = Ito(s)
                    s_rv = s.strip(chars)
                    i_rv = i.str_strip(chars)
                    self.assertEqual(s is s_rv, i is i_rv)
                    self.assertEqual(s_rv, str(i_rv))                           

    # endregion

    # region partition and split methods
    
    def test_str_partition(self):
        basis = f' abc '
        ito = Ito(basis, 1, -1)
        s = basis.strip()

        for sep in [None, '']:
            with self.subTest(sep=sep):
                with self.assertRaises(ValueError):
                    ito.str_partition(sep)

        for sep in ['a', 'b', 'ab', 'bc', 'abc', 'z']:
            with self.subTest(sep=sep):
                s_rv = s.partition(sep)
                i_rv = ito.str_partition(sep)
                
                self.assertEqual(type(s_rv), type(i_rv))
                self.assertEqual(s is s_rv[0], ito is i_rv[0])
                self.assertSequenceEqual(s_rv, tuple(str(i) for i in i_rv))

    def test_str_rpartition(self):
        basis = f' abc '
        ito = Ito(basis, 1, -1)
        s = basis.strip()

        for sep in [None, '']:
            with self.subTest(sep=sep):
                with self.assertRaises(ValueError):
                    ito.str_rpartition(sep)

        for sep in ['a', 'b', 'ab', 'bc', 'abc', 'z']:
            with self.subTest(sep=sep):
                s_rv = s.rpartition(sep)
                i_rv = ito.str_rpartition(sep)
                
                self.assertEqual(type(s_rv), type(i_rv))
                self.assertEqual(s is s_rv[-1], ito is i_rv[-1])
                self.assertSequenceEqual(s_rv, tuple(str(i) for i in i_rv))

    def test_str_rsplit(self):
        for s in ['', ' ', ' a', ' a', ' a ', ' a b', ' a b ', '\ta\nb\rc']:
            for maxsplit in -1, 0, 1:
                with self.subTest(string=s, sep=None, maxsplit=maxsplit):
                    ito = Ito(s)
                    s_rv = s.rsplit(maxsplit=maxsplit)
                    i_rv = ito.str_rsplit(maxsplit=maxsplit)

                    self.assertEqual(type(s_rv), type(i_rv))
                    self.assertEqual(len(s_rv), len(i_rv))
                    for a, b in zip(s_rv, i_rv):
                        self.assertEqual(a is s, b is ito)
                        self.assertEqual(a, str(b))

        basis = f' {"xyz" * 3} '
        ito = Ito(basis, 1, -1)
        s = basis[1:-1]

        sep = ''
        with self.subTest(string=basis, sep=sep):
            with self.assertRaises(ValueError):
                ito.str_rsplit(sep)

        for sep in ['x', 'y', 'xy', 'yz', 'z', 'xyz', 'z']:
            for maxsplit in -1, 0, 1, 2:
                with self.subTest(string=basis, sep=sep, maxsplit=maxsplit):
                    s_rv = s.rsplit(sep, maxsplit=maxsplit)
                    i_rv = ito.str_rsplit(sep, maxsplit=maxsplit)
                    
                    self.assertEqual(type(s_rv), type(i_rv))
                    self.assertEqual(len(s_rv), len(i_rv))
                    for a, b in zip(s_rv, i_rv):
                        self.assertEqual(a is s, b is ito)
                        self.assertEqual(a, str(b))

    def test_str_split_simple(self):
        s = ' A B '
        i = Ito(s, 1, -1)
        expected = str(i).split()
        actual = [str(j) for j in i.str_split()]
        self.assertEqual(expected, actual)

    def test_str_split(self):
        for s in ['', ' ', ' a', ' a', ' a ', ' a b', ' a b ', '\ta\nb\rc', 'a b c d e']:
            for maxsplit in -1, 0, 1:
                with self.subTest(string=s, sep=None, maxsplit=maxsplit):
                    ito = Ito(s)
                    s_rv = s.split(maxsplit=maxsplit)
                    i_rv = ito.str_split(maxsplit=maxsplit)

                    self.assertEqual(type(s_rv), type(i_rv))
                    self.assertEqual(len(s_rv), len(i_rv))
                    for a, b in zip(s_rv, i_rv):
                        self.assertEqual(a is s, b is ito)
                        self.assertEqual(a, str(b))

        basis = f' {"xyz" * 3} '
        ito = Ito(basis, 1, -1)
        s = basis[1:-1]

        sep = ''
        with self.subTest(string=basis, sep=sep):
            with self.assertRaises(ValueError):
                ito.str_split(sep)

        for sep in ['x', 'y', 'xy', 'yz', 'z', 'xyz', 'z']:
            for maxsplit in -1, 0, 1, 2:
                with self.subTest(string=basis, sep=sep, maxsplit=maxsplit):
                    s_rv = s.split(sep, maxsplit=maxsplit)
                    i_rv = ito.str_split(sep, maxsplit=maxsplit)
                    
                    self.assertEqual(type(s_rv), type(i_rv))
                    self.assertEqual(len(s_rv), len(i_rv))
                    for a, b in zip(s_rv, i_rv):
                        self.assertEqual(a is s, b is ito)
                        self.assertEqual(a, str(b))

    def test_str_splitlines(self):
        basis = ''
        ito = Ito(basis)
        s = basis
        with self.subTest(ito=ito, keepends=None):
            s_rv = s.splitlines()
            i_rv = ito.str_splitlines()
            self.assertEqual(type(s_rv), type(i_rv))
            self.assertEqual(len(s_rv), len(i_rv))
            for a, b in zip(s_rv, i_rv):
                self.assertEqual(a is s, b is ito)
                self.assertEqual(a, str(b))

        basis = '\n'
        ito = Ito(basis)
        s = basis
        with self.subTest(ito=ito, keepends=None):
            s_rv = s.splitlines()
            i_rv = ito.str_splitlines()
            self.assertEqual(type(s_rv), type(i_rv))
            self.assertEqual(len(s_rv), len(i_rv))
            for a, b in zip(s_rv, i_rv):
                self.assertEqual(a is s, b is ito)
                self.assertEqual(a, str(b))

        basis = '__'
        ito = Ito(basis, 1, -1)
        s = basis[1:-1]
        with self.subTest(ito=ito, keepends=None):
            s_rv = s.splitlines()
            i_rv = ito.str_splitlines()
            self.assertEqual(type(s_rv), type(i_rv))
            self.assertEqual(len(s_rv), len(i_rv))
            for a, b in zip(s_rv, i_rv):
                self.assertEqual(a is s, b is ito)
                self.assertEqual(a, str(b))

        basis = 'The\nquick\rbrown\r\nfox\vjumped\fover\xc1the\x1dlazy\u2028dogs.'
        paddings = ('', '\n', '\n\n', '\n\n\n', '\u2029', '\u2029\u2029')
        for prefix in paddings:
            for suffix in paddings:
                s = f'{prefix}{basis}{suffix}'
                ito = Ito(s, 1, -1)
                for keepends in True, False:
                    with self.subTest(ito=ito, keepends=keepends):
                        s_rv = s[1:-1].splitlines(keepends=keepends)
                        i_rv = ito.str_splitlines(keepends=keepends)
                        self.assertEqual(type(s_rv), type(i_rv))
                        self.assertEqual(len(s_rv), len(i_rv))
                        for a, b in zip(s_rv, i_rv):
                            self.assertEqual(a is s, b is ito)
                            self.assertEqual(a, str(b))

    # endregion

    def test_str_removeprefix(self):
        basis = '_abc_'
        i = Ito(basis, 1, -1)
        s = basis[1:-1]
        for prefix in '_', 'a':
            with self.subTest(ito=i, prefix=prefix):
                s_rv = s.removeprefix(prefix)
                i_rv = i.str_removeprefix(prefix)
                self.assertEqual(s_rv is s, i_rv is i)
                self.assertEqual(s_rv, str(i_rv))

    def test_str_removesuffix(self):
        basis = '_abc_'
        i = Ito(basis, 1, -1)
        s = basis[1:-1]
        for suffix in '_', 'c':
            with self.subTest(ito=i, suffix=suffix):
                s_rv = s.removesuffix(suffix)
                i_rv = i.str_removesuffix(suffix)
                self.assertEqual(s_rv is s, i_rv is i)
                self.assertEqual(s_rv, str(i_rv))

    def test_str_rfind(self):
        s = 'abcdefgh' * 2
        for ito in Ito(s), Ito(s, 2, -2):
            for find_indices in (None, None), (1, -1):
                for pat in 'ab', 'cd', 'de':
                    with self.subTest(string=s, ito=ito, pattern=pat, start=find_indices[0], stop=find_indices[1]):
                        expected = str(ito).rfind(pat, *find_indices)
                        self.assertEqual(expected, ito.str_rfind(pat, *find_indices))

    def test_str_rindex(self):
        s = ' 12' + 'abcd' * 2 + '34 '
        for ito in Ito(s), Ito(s, 1, -1):
            for find_indices in (None, None), (1, -1), (2, -2), (1, 3):
                for pat in '12', 'ab', 'cd', 'de':
                    with self.subTest(string=s, ito=ito, pattern=pat, start=find_indices[0], stop=find_indices[1]):
                        try:
                            expected = str(ito).rindex(pat, *find_indices)
                            actual = None
                        except ValueError:
                            with self.assertRaises(ValueError):
                                actual = ito.str_rindex(pat, *find_indices)

                        if actual is None:
                            actual = ito.str_rindex(pat, *find_indices)
                            self.assertEqual(expected, actual)

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
