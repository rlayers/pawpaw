import regex
from pawpaw import Ito, Types
from pawpaw.arborform.postorator import WindowedJoin
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
                with self.subTest(string=s, window_size=window_size, desc=desc):
                    wj = WindowedJoin(window_size, func, desc=desc)
                    itos_iter = root.split_iter(re)
                    actual = [*wj(itos_iter)]
                    if len(itos) < window_size:
                        self.assertListEqual(itos, actual)
                    else:
                        joined_count = len(itos) // window_size
                        unjoined_count = len(itos) % window_size
                        self.assertEqual(joined_count + unjoined_count, len(actual))

                        for i in range(0, joined_count):
                            expected = Ito.join(*itos[i * window_size:i * window_size + window_size], desc=desc)
                            self.assertEqual(expected, actual[i])

                        if unjoined_count > 0:
                            tail = itos[-unjoined_count:]
                            self.assertListEqual(tail, actual[-unjoined_count:])
