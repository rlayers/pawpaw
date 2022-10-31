import regex
from segments import Ito
from segments.consolidator import *
from tests.util import _TestIto


class TestWindowedJoin(_TestIto):
    def test_window_size(self):
        func = lambda itos: True
        for window_size in -1, 0, 1, 2:
          with self.subTest(window_size=window_size):
              if window_size < 2:
                  with self.assertRaises(ValueError):
                      WindowedJoin(window_size, func)
              else:
                  WindowedJoin(window_size, func)

    def test_traverse(self):
        func = lambda itos: True
        re = regex.compile(r'\s')
        for s in '', 'One', 'One Two', 'One Two Three', 'One Two Three Four':
            root = Ito(s, desc='root')
            itos = root.split(re)
            desc = 'merged'
            for window_size in 2, 3, 4:
                with self.subTest(string=s, itos=itos, window_size=window_size, desc=desc):
                    m = WindowedJoin(window_size, func, desc)
                    itos_iter = root.split_iter(re)
                    actual = [*m.traverse(itos_iter)]
                    if len(itos) < window_size:
                        self.assertListEqual(itos, actual)
                    elif window_size == 2:
                        self.assertListEqual([root.clone(desc=desc)], actual)
                    else:
                      i = 0
                      stack = []
                      while i < len(itos):
                          needed = window_size - len(stack)
                          stack.extend(itos[i:i + needed])
                          if len(stack) == window_size:
                              joined = Ito.join(stack, desc=desc)
                              stack.clear()
                              stack.append(joined)
                          i += needed
                      self.assertEqual(stack, actual)
