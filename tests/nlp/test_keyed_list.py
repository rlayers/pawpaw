import itertools
import typing

import regex
import pawpaw
from tests.util import _TestIto, IntIto


class TestKeyedList(_TestIto):
    _sample_list_keys = [
        ['1', '2', '3'],
        ['1.1', '1.2', '2.1'],
        ['A', 'B', 'C'],
    ]

    _sample_list_values = [
        'First line.',
        'Second line.',
        'Third line.',
    ]

    def test_itorator(self) -> None:
        itor = pawpaw.nlp.KeyedList().get_itor()

        for sks in self._sample_list_keys:
            for key_sep in ['.', ':']:
                list_lines = [f'{k}{key_sep} {val}' for k, val in zip(sks, self._sample_list_values)]
                for line_sep in ['\n', '\n\r']:
                    _list = pawpaw.Ito(line_sep.join(list_lines))
                    with self.subTest(_list=_list):
                        rv = next(itor(_list), None)
                        self.assertIsNotNone(rv)
                        self.assertEqual('list', rv.desc)
                        self.assertEqual(len(sks), len(rv.children))
