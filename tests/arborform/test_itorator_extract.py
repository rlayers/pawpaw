import itertools

import regex
from pawpaw import Ito
from pawpaw.arborform import Extract
from tests.util import _TestIto


class TestExtract(_TestIto):
    valid_ctor_params = {
        're': [regex.compile(r'(?P<a>.)\s+(?P<b>.)', regex.DOTALL)],
        'limit': [-1, -0, 1, None],
        'desc': ['abc', lambda m, gk: str(gk)],
        'group_filter': [[], ['a', 'b'], lambda m, gk: str(gk) != '0'],
        'tag': ['abc', None],
    }

    def test_ctor_valid(self):
        keys, values = zip(*self.valid_ctor_params.items())
        for kwargs in [dict(zip(keys, v)) for v in itertools.product(*values)]:
            with self.subTest(**kwargs):
                itor = Extract(**kwargs)

    invalid_ctor_params = {
        're': [None, 1, 'abc'],
        'limit': [1.0, 'abc'],
        'desc': [1.1],
        'group_filter': [1],
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
                        itor = Extract(**invalids)

    def test_transform(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )+')
        itor = Extract(re)
        rv = [*itor._transform(root)]
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.desc == k] for k, val in itertools.groupby(itos, lambda x: x.desc)}

        self.assertEqual(3, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.desc)
            self.assertEqual(2, len(phrase.children))

        self.assertEqual(3, len(grouped['word']))
        self.assertTrue(all(w.parent.desc == 'phrase' for w in grouped['word']))

        self.assertEqual(3, len(grouped['number']))
        self.assertTrue(all(n.parent.desc == 'phrase' for n in grouped['number']))

        self.assertEqual(len('teneleventwelve'), len(grouped['char']))
        self.assertTrue(all(c.parent.desc == 'word' for c in grouped['char']))

        self.assertEqual(6, len(grouped['digit']))
        self.assertTrue(all(d.parent.desc == 'number' for d in grouped['digit']))

    def test_group_filter_default(self):
        s = 'abc'
        root = Ito(s)
        name = 'X'
        re = regex.compile(r'.(.).')

        extract = Extract(re)
        expected = root.clone(1, 2, desc='1')
        rv = [*extract(root)]
        self.assertEqual(1, len(rv))
        self.assertEqual(expected, rv[0])
        self.assertSequenceEqual([*expected.children], [*rv[0].children])

    def test_group_filter_inverse_tautology(self):
        s = 'abc'
        root = Ito(s)
        name = 'X'
        re = regex.compile(r'.(.).')

        extract = Extract(re, group_filter=lambda match, gk: False)
        rv = [*extract(root)]
        self.assertEqual(0, len(rv))

    def test_named_and_unnamed_groups_present_in_match(self):
        s = 'AB'
        root = Ito(s)
        re = regex.compile(r'(.)(?<foo>.)')

        extract = Extract(re)
        expected = [root.clone(0, 1, '1'), root.clone(1, 2, 'foo')]
        rv = [*extract(Ito(s))]
        self.assertListEqual(expected, rv)

    def test_desc(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )+')
        df = lambda m, gk: str(gk) + 'x' if str(gk) == 'char' else str(gk)
        itor = Extract(re, desc=df)
        rv = itor._transform(root)
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.desc == k] for k, val in itertools.groupby(itos, lambda x: x.desc)}

        self.assertEqual(3, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.desc)
            self.assertEqual(2, len(phrase.children))

        self.assertEqual(3, len(grouped['word']))
        self.assertTrue(all(w.parent.desc == 'phrase' for w in grouped['word']))

        self.assertEqual(3, len(grouped['number']))
        self.assertTrue(all(n.parent.desc == 'phrase' for n in grouped['number']))

        self.assertEqual(len('teneleventwelve'), len(grouped['charx']))
        self.assertTrue(all(c.parent.desc == 'word' for c in grouped['charx']))

        self.assertEqual(6, len(grouped['digit']))
        self.assertTrue(all(d.parent.desc == 'number' for d in grouped['digit']))

    def test_limit(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )')
        limit = 2
        itor = Extract(re, limit=2)
        rv = itor._transform(root)

        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.desc == k] for k, val in itertools.groupby(itos, lambda x: x.desc)}

        self.assertEqual(limit, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.desc)
            self.assertEqual(2, len(phrase.children))

        self.assertEqual(limit, len(grouped['word']))
        self.assertTrue(all(w.parent.desc == 'phrase' for w in grouped['word']))

        self.assertEqual(limit, len(grouped['number']))
        self.assertTrue(all(n.parent.desc == 'phrase' for n in grouped['number']))

        self.assertEqual(len('teneleven'), len(grouped['char']))
        self.assertTrue(all(c.parent.desc == 'word' for c in grouped['char']))

        self.assertEqual(4, len(grouped['digit']))
        self.assertTrue(all(d.parent.desc == 'number' for d in grouped['digit']))

    def test_group_filter_list(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )+')
        gf = ('phrase', 'word')
        itor = Extract(re, group_filter=gf)
        rv = itor._transform(root)
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.desc == k] for k, val in itertools.groupby(itos, lambda x: x.desc)}

        self.assertEqual(3, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.desc)
            self.assertEqual(1, len(phrase.children))

        self.assertEqual(3, len(grouped['word']))
        self.assertTrue(all(w.parent.desc == 'phrase' for w in grouped['word']))

        self.assertIsNone(grouped.get('number', None))
        self.assertIsNone(grouped.get('char', None))
        self.assertIsNone(grouped.get('digit', None))

    def test_group_filter_lambda(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )+')
        gf = lambda m, gk: gk in ('phrase', 'number')
        itor = Extract(re, group_filter=gf)
        rv = itor._transform(root)
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.desc == k] for k, val in itertools.groupby(itos, lambda x: x.desc)}

        self.assertEqual(3, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.desc)
            self.assertEqual(1, len(phrase.children))

        self.assertIsNone(grouped.get('word', None))

        self.assertEqual(3, len(grouped['number']))
        self.assertTrue(all(w.parent.desc == 'phrase' for w in grouped['number']))

        self.assertIsNone(grouped.get('char', None))
        self.assertIsNone(grouped.get('digit', None))
