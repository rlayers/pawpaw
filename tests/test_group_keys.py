import regex
from pawpaw import GroupKeys
from tests.util import _TestIto


class TestGroupKeys(_TestIto):
    def test_preferred(self):
        for pat in r'.', r'(?P<key1>.).(?P<key2>.)':
            with self.subTest(re=pat):
                re = regex.compile(pat)
                pgks = GroupKeys.preferred(re)
                self.assertEqual(re.groups + 1, len(pgks))
                for i, gk in enumerate(pgks):
                    if isinstance(gk, str):
                        self.assertEqual(i, re.groupindex[gk])
                    else:
                        self.assertEqual(i, gk)

    def test_validate(self):
        re = regex.compile(r'(?P<key1>.).(?P<key2>.)')
        
        for valid_gks in [[0], [0, 1, 2], ['key1'], ['key1', 'key2'], [0, 'key2'], GroupKeys.preferred(re)]:
            with self.subTest(group_keys=valid_gks):
                GroupKeys.validate(re, valid_gks)

        for invalid_gks in [[-1], [0, 3], ['xyz'], ['key1', 'key1'], [1, 'key1'], ['key1', 1]]:
            with self.subTest(group_keys=valid_gks):
                with self.assertRaises(ValueError):
                    GroupKeys.validate(re, invalid_gks)
