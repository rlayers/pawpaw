import itertools
import typing

import regex
from pawpaw import Ito
from pawpaw.arborform import Itorator, Split
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
        elif brt == Split.BoundaryRetention.ALL:
            rv = rv[:1] + list(itertools.chain.from_iterable((sep, i) for i in rv[1:]))

        return rv
    
    valid_ctor_params = {
        'splitter': [Itorator.wrap(lambda ito: ito.str_split()), regex.compile(r'\s+', regex.DOTALL)],
        'limit': [-1, -0, 1, None],
        'boundary_retention': list(Split.BoundaryRetention),
        'return_zero_split': [False, True],
        'desc': ['abc', None],
        'tag': ['abc', None],
    }

    def test_ctor_valid(self):
        keys, values = zip(*self.valid_ctor_params.items())
        for kwargs in [dict(zip(keys, v)) for v in itertools.product(*values)]:
            with self.subTest(**kwargs):
                itor = Split(**kwargs)

    invalid_ctor_params = {
        'splitter': [None, True, 1, 'abc'],
        'limit': [1.0, 'abc'],
        'boundary_retention': [None, True, 1, 'abc'],
        'return_zero_split': [None, 1, 'abc'],
        'desc': [True, 1],
        'tag': [True, 1.3],
    }

    def test_ctor_invalid(self):
        valids = {k: v[0] for k, v in self.valid_ctor_params.items()}
        for k, vs in self.invalid_ctor_params.items():
            invalids = dict(**valids)
            for v in vs:
                invalids[k] = v
                with self.subTest(**invalids):
                    with self.assertRaises(TypeError):
                        itor = Split(**invalids)

    def test_iter_simple(self):
        for sep in ' ', '-':  # '', ' ', '-':
            s = self.str_from(sep)
            ito = Ito(s, desc='root')
            re = self.re_from(sep)
            for brt in Split.BoundaryRetention:
                with self.subTest(string=s, separator=sep, boundary_retention=brt):
                    expected = self.expected_from(s, sep, brt)
                    non_sep_desc = 'split'
                    split = Split(re, boundary_retention=brt, desc=non_sep_desc)
                    actual = [*split._transform(ito)]
                    self.assertListEqual(expected, [str(i) for i in actual])
                    self.assertTrue(all(i.desc in (None, non_sep_desc) for i in actual))

    def test_iter_sep_not_present(self):
        sep = 'XXX'
        s = self.str_from(' ')
        ito = Ito(s)
        re = regex.compile(regex.escape(sep))
        desc='post-split'
        for brt in Split.BoundaryRetention:
            for return_zero_split in True, False:
                with self.subTest(string=s, separator=sep, boundary_retention=brt, return_zero_split=return_zero_split, desc=desc):
                    expected = [ito.clone(desc=desc)] if return_zero_split else []
                    split = Split(re, boundary_retention=brt, return_zero_split=return_zero_split, desc=desc)
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
                    split = Split(re, boundary_retention=brt, desc=desc)
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
                
