from pawpaw.visualization.sgr import *
from tests.util import _TestIto


class TestSgr(_TestIto):
    def test_sgr_reset_all(self):
        self.assertTrue(f'\033[0m', RESET_ALL)
        
    def test_sgr_encode(self):
        for vals in (0,), (1,), (1,2,3):
            with self.subTest(value=vals):
                vals_str = ';'.join(str(v) for v in vals)
                expected = f'\033[{vals_str}m'
                actual = encode(*vals)
                self.assertEqual(expected, actual)
                self.assertFalse(actual.isprintable())
