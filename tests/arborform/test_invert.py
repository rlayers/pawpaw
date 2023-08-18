import regex
from pawpaw import Ito
from pawpaw.arborform import Extract, Invert
from tests.util import _TestIto


class TestInvert(_TestIto):
    def test_transform(self):
        s = ' a1b2c '
        root = Ito(s)

        non_gap_desc = 'nongap'
        gap_desc = 'gap'

        extract_res = [
            regex.compile(r'.', regex.DOTALL),
            regex.compile(r'\s', regex.DOTALL),
            regex.compile(r'[a-z]', regex.DOTALL),
            regex.compile(r'\d', regex.DOTALL),
            regex.compile(r'\S', regex.DOTALL),
            regex.compile(r'_', regex.DOTALL),
        ]

        for re in extract_res:
            with self.subTest(re=re.pattern):
                itor_extract = Extract(re, desc_func=lambda ito, match, group_key: non_gap_desc, group_filter = None)
                non_gaps = [*itor_extract(root)]
                expected = [*Ito.from_gaps(root, non_gaps, gap_desc)]

                itor_gaps = Invert(itor_extract, desc=gap_desc)
                self.assertSequenceEqual(expected, [*itor_gaps(root)])
