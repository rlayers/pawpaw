import unittest

import pawpaw


class TestVersion(unittest.TestCase):

    _valid_versions = [
        '1.dev0',
        '1.0.dev456',
        '1.0a1',
        '1.0a2.dev456',
        '1.0a12.dev456',
        '1.0a12',
        '1.0b1.dev456',
        '1.0b2',
        '1.0b2.post345.dev456',
        '1.0b2.post345',
        '1.0rc1.dev456',
        '1.0rc1',
        '1.0',
        '1.0+abc.5',
        '1.0+abc.7',
        '1.0+5',
        '1.0.post456.dev34',
        '1.0.post456',
        '1.0.15',
        '1.1.dev1',
    ]
    # Taken from https://peps.python.org/pep-0440/#summary-of-permitted-suffixes-and-relative-ordering

    def test_is_canonical_valid(self):
        for v in self._valid_versions:
             with self.subTest(version=v):
                self.assertTrue(pawpaw.Version.is_canonical(v))

    _invalid_versions = [
        '1.0a',
        '1.0dev0',
        '1.0post',
        '1.0d1',
    ]

    def test_is_canonical_invalid(self):
        for v in self._invalid_versions:
             with self.subTest(version=v):
                self.assertFalse(pawpaw.Version.is_canonical(v))

    def test_version_parse_re(self):
        v = '1.2a34.dev567+xyz.8'
        m = pawpaw.Version.parse_re.fullmatch(v)
        self.assertIsNotNone(m)
        ito = pawpaw.Ito.from_match(m)[0]

        tests: list[tuple[str]] = [
            ('release', '*[d:release]', '1.2'),

            ('pre', '*[d:pre]', 'a34'),
            ('pre_l', '*[d:pre]/*[d:pre_l]', 'a'),
            ('pre_n', '*[d:pre]/*[d:pre_n]', '34'),

            ('dev', '*[d:dev]', '.dev567'),
            ('dev_l', '*[d:dev]/*[d:dev_l]', 'dev'),
            ('dev_n', '*[d:dev]/*[d:dev_n]', '567'),

            ('local', '*[d:local]', 'xyz.8'),
        ]

        for name, path, expected in tests:
            with self.subTest(component=name):
                val = ito.find(path)
                self.assertEqual(expected, str(val))
