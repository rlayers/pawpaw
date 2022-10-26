import regex
from segments import Ito
from tests.util import _TestIto


class TestItoRegexEquivalenceMethods(_TestIto):
    def test_regex_finditer(self):
        strings = '', 'A', 'Here are some words.'
        paddings = '', ' ', '_'
        for string in strings:
            for padding in paddings:
                s = f'{padding}{string}{padding}'
                pad_slice = slice(len(padding), -len(padding))
                ito = Ito(s, pad_slice.start, pad_slice.stop)
                for re_str in r' ', r'\w+', r'(?P<Word>\w+)':
                    re = regex.compile(re_str, regex.DOTALL)
                    with self.subTest(string=s, ito=ito, pattern=re.pattern):
                        expected = [*re.finditer(s, pos=pad_slice.start, endpos=pad_slice.stop)]
                        actual = [*ito.regex_finditer(re)]
                        self.assertEqual(len(expected), len(actual))
                        for e, a in zip(expected, actual):
                            self.assertEqual(e, a)

    def test_regex_match(self):
        strings = '', 'A', 'Here are some words.'
        paddings = '', ' ', '_'
        for string in strings:
            for padding in paddings:
                s = f'{padding}{string}{padding}'
                pad_slice = slice(len(padding), -len(padding))
                ito = Ito(s, pad_slice.start, pad_slice.stop)
                for re_str in r' ', r'\w+', r'(?P<Word>\w+)':
                    re = regex.compile(re_str, regex.DOTALL)
                    with self.subTest(string=s, ito=ito, pattern=re.pattern):
                        expected = re.match(s, pos=pad_slice.start, endpos=pad_slice.stop)
                        actual = ito.regex_match(re)
                        self.assertEqual(expected, actual)

    def test_regex_search(self):
        strings = '', 'A', 'Here are some words.'
        paddings = '', ' ', '_'
        for string in strings:
            for padding in paddings:
                s = f'{padding}{string}{padding}'
                pad_slice = slice(len(padding), -len(padding))
                ito = Ito(s, pad_slice.start, pad_slice.stop)
                for re_str in r' ', r'\w+', r'(?P<Word>\w+)':
                    re = regex.compile(re_str, regex.DOTALL)
                    with self.subTest(string=s, ito=ito, pattern=re.pattern):
                        expected = re.search(s, pos=pad_slice.start, endpos=pad_slice.stop)
                        actual = ito.regex_search(re)
                        self.assertEqual(expected, actual)

    def test_regex_split_simnple(self):
        strings = '', 'A', 'Here are some words.'
        separators = ' ', '\n', '\r\n'
        paddings = '', ' ', '_'
        for string in strings:
            for sep in separators:
                s = string.replace(' ', sep)
                for padding in paddings:
                    s = f'{padding}{s}{padding}'
                    pad_slice = slice(len(padding), -len(padding))
                    ito = Ito(s, pad_slice.start, pad_slice.stop)
                    re = regex.compile(regex.escape(sep), regex.DOTALL)
                    with self.subTest(string=s, ito=ito, pattern=re.pattern):
                        expected = re.split(s[pad_slice])
                        actual = ito.regex_split(re)
                        self.assertListEqual(expected, actual)

    def test_regex_split_sep_not_present(self):
        strings = '', 'A', 'Here are some words.'
        separator = 'XXX'
        paddings = '', ' ', '_'
        for string in strings:
            for padding in paddings:
                s = f'{padding}{string}{padding}'
                pad_slice = slice(len(padding), -len(padding))
                ito = Ito(s, pad_slice.start, pad_slice.stop)
                re = regex.compile(regex.escape(seperator), regex.DOTALL)
                with self.subTest(string=s, ito=ito, pattern=re.pattern):
                    expected = re.split(s[pad_slice])
                    actual = ito.regex_split(re)
                    self.assertListEqual(expected, actual)
