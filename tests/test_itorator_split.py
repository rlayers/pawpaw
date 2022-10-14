import typing

import regex
from segments import Ito
from segments.itorator import Split
from tests.util import _TestIto


class TestSplit(_TestIto):
    PREFIX = 'PRE'
    MIDDLE = 'MID'
    SUFFIX = 'SUF'
  
    @classmethod
    def str_from(cls, sep: str) -> str:
        return sep.join((cls.PREFIX, cls.MIDDLE, cls.MIDDLE, cls.SUFFIX))
    
    @classmethod
    def re_from(cls, sep: str) -> regex.Pattern:
        return regex.compile(regex.escape(sep), regex.DOTALL)
    
    @classmethod
    def expected_from(cls, s: str, sep: str, brt: Split.BoundaryRetention) -> typing.List[str]:
        if sep == '':
            return [c for c in s]
      
        rv = s.split(sep)
        if brt == Split.BoundaryRetention.LEADING:
            del rv[0]
            for i, s in enumerate(rv):
                rv[i] = sep + s
        elif brt == Split.BoundaryRetention.TRAILING:
            del rv[-1]
            for i, s in enumerate(rv):
                rv[i] += sep

        return rv
    
    def test_iter(self):
        for sep in ' ', '-':  # '', ' ', '-':
            s = self.str_from(sep)
            ito = Ito(s, desc='root')
            re = self.re_from(sep)
            for brt in Split.BoundaryRetention:
                with self.subTest(string=s, separator=sep, boundary_retention=brt):
                    expected = self.expected_from(s, sep, brt)
                    desc = 'split'
                    split = Split(re, boundary_retention=brt, desc=desc)
                    actual = split._iter(ito)
                    self.assertSequenceEqual(expected, [i[:] for i in actual])
                    self.assertTrue(all(i.desc == desc for i in actual))
