from segments import Span, Ito
from tests.util import _TestIto


class TestSpan(_TestIto):
    def test_from_indices_valid(self):
        for s in '', ' ', ' abc ':
            for start in (-100, -1, None, 0, 1, 100):
                for stop in (-100, -1, None, 0, 1, 100):
                    if len(s) == 0:
                        ito = Ito(s)
                    elif len(s) == 1:
                        ito = Ito(s, 1)
                    else:
                        ito = Ito(s, 1, -1)

                    for basis in s, ito:
                        with self.subTest(basis=basis, start=start, stop=stop):
                            _slice = slice(start, stop)
                            expected = basis[_slice]
                            span = Span.from_indices(basis, start, stop)
                            actual = basis[slice(*span)]
                            self.assertEqual(expected, actual)

    def test_from_indices_invalid_base(self):
        for basis in [None, 1.0]:
            with self.subTest(basis=basis):
                with self.assertRaises(TypeError):
                    Span.from_indices(basis)

    def test_from_indices_invalid_indices(self):
        s = 'abc'
        for k, v in {'start': 1.0, 'stop': 1.0}.items():
            with self.subTest(basis=s, **{k: v}):
                with self.assertRaises(TypeError):
                    Span.from_indices(s, **{k: v})
                    
    def test_offset(self):
        s = 'abc'
        for basis in s, Ito(s, 1, -1):
            for i in -100, -1, 0, 1, 100:
                with self.subTest(basis=basis, i=i):
                    span = Span.from_indices(basis)
                    if (span.start + i < 0) or (span.stop + i < 0):
                        with self.assertRaises(ValueError):
                            span.offset(i)
                    else:
                        rv = span.offset(i)
                        self.assertEquals(span.start + i, rv.start)
                        self.assertEquals(span.stop + i, rv.stop)
