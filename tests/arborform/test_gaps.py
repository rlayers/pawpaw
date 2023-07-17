import regex
from pawpaw import Ito
from pawpaw.arborform import Extract, Gaps
from tests.util import _TestIto


class TestGaps(_TestIto):
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
        ]

        for re in extract_res:
            with self.subTest(re=re.pattern):
                itor_extract = Extract(re, desc_func=lambda ito, match, group_key: gap_desc, group_filter = None)
                non_gaps = [*itor_extract(root)]
                gaps = [*Ito.from_gaps(root, non_gaps, gap_desc)]
                expected = list(non_gaps)
                expected.extend(gaps)
                expected.sort(key=lambda ito: ito.start)

                itor_gaps = Gaps(itor_extract, desc=gap_desc)
                self.assertSequenceEqual(expected, [*itor_gaps(root)])
