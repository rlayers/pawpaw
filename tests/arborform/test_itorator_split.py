import itertools
import typing

import regex
from pawpaw import Ito
from pawpaw.arborform import Split
from tests.util import _TestIto


class TestSplit(_TestIto):
    PREFIX = 'PRE'
    MIDDLE = 'MID'
    SUFFIX = 'SUF'
  
    @classmethod
    def str_from(cls, sep: str) -> str:
        return sep.join((cls.PREFIX, cls.MIDDLE, cls.MIDDLE, cls.SUFFIX))
    
    SEP_DESC = 'sep'

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
        elif brt == Split.BoundaryRetention.DISTINCT:
            rv = rv[:1] + list(itertools.chain.from_iterable((sep, i) for i in rv[1:]))

        return rv
    
    def test_iter_simple(self):
        for sep in ' ', '-':  # '', ' ', '-':
            s = self.str_from(sep)
            ito = Ito(s, desc='root')
            re = self.re_from(sep)
            for brt in Split.BoundaryRetention:
                with self.subTest(string=s, separator=sep, boundary_retention=brt):
                    expected = self.expected_from(s, sep, brt)
                    non_sep_desc = 'split'
                    split = Split(re, boundary_retention=brt, boundary_desc=self.SEP_DESC, non_boundary_desc=non_sep_desc)
                    actual = [*split._transform(ito)]
                    self.assertListEqual(expected, [str(i) for i in actual])
                    self.assertTrue(all(i.desc in (self.SEP_DESC, non_sep_desc) for i in actual))

    def test_iter_sep_not_present(self):
        sep = 'XXX'
        s = self.str_from(' ')
        ito = Ito(s)
        re = regex.compile(regex.escape(sep))
        desc='post-split'
        for brt in Split.BoundaryRetention:
            for return_zero_split in True, False:
                with self.subTest(string=s, separator=sep, boundary_retention=brt, return_zero_split=return_zero_split, non_boundary_desc=desc):
                    expected = [ito.clone(desc=desc)] if return_zero_split else []
                    split = Split(re, boundary_retention=brt, return_zero_split=return_zero_split, non_boundary_desc=desc)
                    actual = [*split._transform(ito)]
                    self.assertListEqual(expected, actual)

    @classmethod
    def zero_width_patterns(cls, sep: str) -> typing.Iterable[regex.Pattern]:
        esc_sep = regex.escape(sep)
        yield r'(?<=' + esc_sep + r')'  # look behind
        yield r'(?=' + esc_sep + r')'  # look ahead
    
    def test_iter_zero_width_matches(self):
        sep = '.'
        s = self.str_from(sep)
        ito = Ito(s, desc='root')
        for pat in self.zero_width_patterns(sep):
            re = regex.compile(pat)
            for brt in Split.BoundaryRetention:
                with self.subTest(string=s, pattern=pat, boundary_retention=brt):
                    expected = re.split(s)
                    if brt == Split.BoundaryRetention.LEADING:
                        del expected[0]
                    elif brt == Split.BoundaryRetention.TRAILING:
                        del expected[-1]
                    desc = 'split'
                    split = Split(re, boundary_retention=brt, non_boundary_desc=desc)
                    actual = [*split._transform(ito)]
                    self.assertListEqual(expected, [str(i) for i in actual])
                    self.assertTrue(all(i.desc == desc for i in actual))

    def test_limit(self):
        s = 'abc'
        root = Ito(s)
        
        re = regex.compile('(?=.)')
        for limit in None, *range(0, len(s)):
            with self.subTest(re=re.pattern, limit=limit):
                splitter = Split(re, limit=limit)
                rv = [*splitter(root)]
                expected = []
                if limit is None:
                    expected.extend(root)
                elif limit == 0:
                    expected.append(root)
                else:
                    expected.extend(i for i in root[:limit-1] if len(i) > 0)  # split parts
                    expected.append(root.clone(limit-1))  # remaining part
                self.assertSequenceEqual(expected, rv)

        re = regex.compile('(?<=.)')
        for limit in None, *range(0, len(s)):
            with self.subTest(re=re.pattern, limit=limit):
                splitter = Split(re, limit=limit)
                rv = [*splitter(root)]
                expected = []
                if limit is None:
                    expected.extend(root)
                elif limit == 0:
                    expected.append(root)
                else:
                    expected.extend(i for i in root[:limit] if len(i) > 0)  # split parts
                    expected.append(root.clone(limit))  # remaining part
                self.assertSequenceEqual(expected, rv)

        re = regex.compile('b')
        for limit in None, *range(0, len(s)):
            with self.subTest(re=re.pattern, limit=limit):
                splitter = Split(re, limit=limit)
                rv = [*splitter(root)]
                expected = []
                if limit is None or limit > 0:
                    expected.extend(root.str_split('b'))
                else:
                    expected.append(root)
                self.assertSequenceEqual(expected, rv)
                
