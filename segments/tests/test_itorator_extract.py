import itertools
import typing

import regex
from segments import Ito
from segments.itorator import Extract
from segments.tests.util import _TestIto


class TestExtract(_TestIto):
    def test_iter(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )+')
        itor = Extract(re)
        rv = itor._iter(root)
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.descriptor == k] for k, val in itertools.groupby(itos, lambda x: x.descriptor)}

        self.assertEqual(3, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.descriptor)
            self.assertEqual(2, len(phrase.children))

        self.assertEqual(3, len(grouped['word']))
        self.assertTrue(all(w.parent.descriptor == 'phrase' for w in grouped['word']))

        self.assertEqual(3, len(grouped['number']))
        self.assertTrue(all(n.parent.descriptor == 'phrase' for n in grouped['number']))

        self.assertEqual(len('teneleventwelve'), len(grouped['char']))
        self.assertTrue(all(c.parent.descriptor == 'word' for c in grouped['char']))

        self.assertEqual(6, len(grouped['digit']))
        self.assertTrue(all(d.parent.descriptor == 'number' for d in grouped['digit']))

    def test_descriptor_func(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )+')
        df = lambda i, m, g: g + 'x' if g == 'char' else g
        itor = Extract(re, descriptor_func=df)
        rv = itor._iter(root)
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.descriptor == k] for k, val in itertools.groupby(itos, lambda x: x.descriptor)}

        self.assertEqual(3, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.descriptor)
            self.assertEqual(2, len(phrase.children))

        self.assertEqual(3, len(grouped['word']))
        self.assertTrue(all(w.parent.descriptor == 'phrase' for w in grouped['word']))

        self.assertEqual(3, len(grouped['number']))
        self.assertTrue(all(n.parent.descriptor == 'phrase' for n in grouped['number']))

        self.assertEqual(len('teneleventwelve'), len(grouped['charx']))
        self.assertTrue(all(c.parent.descriptor == 'word' for c in grouped['charx']))

        self.assertEqual(6, len(grouped['digit']))
        self.assertTrue(all(d.parent.descriptor == 'number' for d in grouped['digit']))

    def test_limit(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )')
        limit = 2
        itor = Extract(re, limit=2)
        rv = itor._iter(root)

        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.descriptor == k] for k, val in itertools.groupby(itos, lambda x: x.descriptor)}

        self.assertEqual(limit, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.descriptor)
            self.assertEqual(2, len(phrase.children))

        self.assertEqual(limit, len(grouped['word']))
        self.assertTrue(all(w.parent.descriptor == 'phrase' for w in grouped['word']))

        self.assertEqual(limit, len(grouped['number']))
        self.assertTrue(all(n.parent.descriptor == 'phrase' for n in grouped['number']))

        self.assertEqual(len('teneleven'), len(grouped['char']))
        self.assertTrue(all(c.parent.descriptor == 'word' for c in grouped['char']))

        self.assertEqual(4, len(grouped['digit']))
        self.assertTrue(all(d.parent.descriptor == 'number' for d in grouped['digit']))

    def test_group_filter_list(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )+')
        gf = ('phrase', 'word')
        itor = Extract(re, group_filter=gf)
        rv = itor._iter(root)
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.descriptor == k] for k, val in itertools.groupby(itos, lambda x: x.descriptor)}

        self.assertEqual(3, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.descriptor)
            self.assertEqual(1, len(phrase.children))

        self.assertEqual(3, len(grouped['word']))
        self.assertTrue(all(w.parent.descriptor == 'phrase' for w in grouped['word']))

        self.assertIsNone(grouped.get('number', None))
        self.assertIsNone(grouped.get('char', None))
        self.assertIsNone(grouped.get('digit', None))

    def test_group_filter_lambda(self):
        s = 'ten 10 eleven 11 twelve 12 '
        root = Ito(s)
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+) )+')
        gf = lambda i, m, g: g in ('phrase', 'number')
        itor = Extract(re, group_filter=gf)
        rv = itor._iter(root)
        itos = rv + [*itertools.chain(*(i.walk_descendants() for i in rv))]
        grouped = {k: [v for v in itos if v.descriptor == k] for k, val in itertools.groupby(itos, lambda x: x.descriptor)}

        self.assertEqual(3, len(grouped['phrase']))
        for phrase in grouped['phrase']:
            self.assertEqual('phrase', phrase.descriptor)
            self.assertEqual(1, len(phrase.children))

        self.assertIsNone(grouped.get('word', None))

        self.assertEqual(3, len(grouped['number']))
        self.assertTrue(all(w.parent.descriptor == 'phrase' for w in grouped['number']))

        self.assertIsNone(grouped.get('char', None))
        self.assertIsNone(grouped.get('digit', None))
