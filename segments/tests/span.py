from segments import Span
from segments.tests.util import _TestIto, RandSubstrings


class TestSpan(_TestIto):
    def test_from_indices_valid(self):
        for basis in ['', ' ', ' abc ']:
              with self.subTest(basis=basis):
                  for start in (-100, -1, None, 0, 1, 100):
                      with self.subTest(start=start):
                          for stop in (-100, -1, None, 0, 1, 100):
                              with self.subTest(stop=stop):
                                    _slice = slice(start, stop)
                                    expected = basis[_slice]
                                    span = Span.from_indices(basis, start, stop)
                                    self.assertEqual(expected, string[span.start:span.stop])
                                    self.assertEqual(expected, basis[slice(*span)])

    def test_from_indices_invalid_base(self):
        for basis in [None, 1.0]:
          with self.subTest(basis=basis):
              with self.assertRaises(TypeError):
                  Span.from_indices(basis)

    def test_from_indices_invalid_indices(self):
        s = 'abc'
        for k, v in {'start': 1.0, 'stop': 1.0}.items():
            with self.SubTest(basis=s, **{k:v}):
                with self.assertRaises(TypeError):
                    Span.from_indices(s, **{k:v})
