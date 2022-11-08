import regex
from segments import Ito
from segments.consolidator import *
from tests.util import _TestIto


class TestWindowedJoinEx(_TestIto):
    def test_window_size(self):
        func = lambda itos: True
        for window_size in -1, 0, 1, 2:
          with self.subTest(window_size=window_size):
              if window_size < 2:
                  with self.assertRaises(ValueError):
                      WindowedJoinEx(window_size, func)
              else:
                  WindowedJoinEx(window_size, func)

    def test_traverse(self):
        func = lambda itos: True
        re = regex.compile(r'\s')
        for s in '', 'One', 'One Two', 'One Two Three', 'One Two Three Four':
            root = Ito(s, desc='root')
            itos = root.split(re)
            desc = 'merged'
            for window_size in 2, 3, 4:
                with self.subTest(string=s, itos=itos, window_size=window_size, desc=desc):
                    wj = WindowedJoinEx(window_size, func, desc)
                    itos_iter = root.split_iter(re)
                    actual = [*m.traverse(itos_iter)]
                    if len(itos) < window_size:
                        self.assertListEqual([Types.C_BITO(True, i) for i in itos], actual)
                    else:
                        while len(actual) >= window_size:
                            self.assertTrue(all(not bi.tf for bi in actual[:window_size]))
                            del actual[:window_size]
                            if len(actual) > 0:
                                self.assertTrue(actual[0].tf)
                                del actual[0]

                        self.assertTrue(all(bi.tf for bi in actual))
