import itertools
import typing

import regex
from pawpaw import Ito, Types, arborform
from pawpaw.arborform import Itorator, Connectors, Postorator
from tests.util import _TestIto


class TestItoratorConnections(_TestIto):
    def test_yield_break(self):
        s = '123a321'
        root = Ito(s)

        itor_1 = Itorator.wrap(lambda ito: [ito.str_strip('1')])
        itor_2 = Itorator.wrap(lambda ito: [ito.str_strip('2')])
        itor_3 = Itorator.wrap(lambda ito: [ito.str_strip('3')])
        
        itor_1.connections.append(Connectors.Delegate(itor_2))
        itor_1.connections.append(Connectors.Delegate(itor_3))
        rv = [*itor_1(root)]

        self.assertSequenceEqual([Ito(root, 2, -2)], rv)

        itor_1.connections.clear()
        itor_1.connections.append(Connectors.Delegate(itor_2))
        itor_2.connections.append(Connectors.Delegate(itor_3))
        rv = [*itor_1(root)]

        self.assertSequenceEqual([Ito(root, 3, -3)], rv)

    def test_assign(self):
        s = '123a321'
        root = Ito(s)

        itor_1 = Itorator.wrap(lambda ito: [ito.str_strip('1')])
        itor_2 = Itorator.wrap(lambda ito: [ito.str_strip('2')])
        itor_3 = Itorator.wrap(lambda ito: [ito.str_strip('3')])
        
        itor_1.connections.append(Connectors.Recurse(itor_2))
        itor_1.connections.append(Connectors.Recurse(itor_3))
        rv = [*itor_1(root)]

        self.assertSequenceEqual([Ito(root, 3, -3)], rv)

        itor_1.connections.clear()
        itor_1.connections.append(Connectors.Recurse(itor_2))
        itor_2.connections.append(Connectors.Recurse(itor_3))
        rv = [*itor_1(root)]

        self.assertSequenceEqual([Ito(root, 3, -3)], rv)

    def test_sub(self):
        s = '123a321'
        root = Ito(s)

        itor_1 = Itorator.wrap(lambda ito: [ito.str_strip('1')])
        itor_2 = Itorator.wrap(lambda ito: [ito.str_strip('2')])
        
        itor_1.connections.append(Connectors.Subroutine(itor_2))
        rv = [*itor_1(root)]

        self.assertSequenceEqual([Ito(root, 1, -1)], rv)

        def sec_desc_x(ito) -> typing.Iterable[Ito]:
            ito.desc = 'x'
            return  # don't yield anything
            yield  # this forces interpretation as a generator method
        itor_2 = Itorator.wrap(sec_desc_x)

        itor_1.connections.clear()
        itor_1.connections.append(Connectors.Subroutine(itor_2))
        actual = [*itor_1(root)]

        self.assertSequenceEqual([Ito(root, 1, -1, 'x')], actual)
        
    def test_connect_recurse(self):
        s = ' abc '
        root = Ito(s, 1, -1)
        desc = 'x'
        itor_r = arborform.Reflect()
        itor_d = arborform.Desc(desc)

        lambdas = {
            '[default]': None,
            'Always True': lambda ito: True,
            'Always False': lambda ito: False,
        }

        for lam_desc, lam_f in lambdas.items():
            with self.subTest(lambda_=lam_desc):
                itor_r.connections.clear()

                if lam_f is None:
                    itor_r.connections.append(Connectors.Recurse(itor_d))
                else:
                    itor_r.connections.append(Connectors.Recurse(itor_d, lam_f))
                
                if lam_f is None or lam_f(root):
                    expected = root.clone(desc=desc)
                else:
                    expected = root

                actual = next(itor_r(root))
                self.assertEqual(expected, actual)

    # def test_connect_sub(self):
    #     s = ' one 123 two 456 '
    #     root = Ito(s, 1, -1)
        
    #     itor_r = self.get_reflect()

    #     # create sub-pipeline with two endpoints
    #     itor_tok_split = Itorator.wrap(lambda ito: ito.str_split())
    #     con = Connectors.Sub(itor_tok_split)
    #     itor_r.connections.append(con)

    #     itor_desc_word = self.get_desc('word')
    #     con = Connectors.Next(itor_desc_word, lambda ito: not ito.str_isnumeric())
    #     itor_tok_split.connections.append(con)

    #     itor_desc_num = self.get_desc('number')
    #     con = Connectors.Next(itor_desc_num)
    #     itor_tok_split.connections.append(con)

    #     # ensure this works as expected
    #     rv = [*itor_r(root)]
    #     self.assertEqual(len(root.str_split()), len(rv))
    #     self.assertTrue(all(i.desc in ['word', 'number'] for i in rv))

    #     # now add a Next connection AFTER the sub-pipeline
    #     def prepend_x(ito) -> Types.C_IT_ITOS:
    #         ito.desc = 'x' + ito.desc
    #         return ito,
    #     itor_desc_pre_x = Itorator.wrap(prepend_x)
    #     con = Connectors.Next(itor_desc_pre_x)
    #     itor_r.connections.append(con)

    #     # ensure next connects to all the sub-pipeline's endpoints
    #     rv = [*itor_r(root)]
    #     self.assertEqual(len(root.str_split()), len(rv))
    #     self.assertTrue(all(i.desc.startswith('x') for i in rv))

    def test_connect_children(self):
        s = ' one 123 two 456 '
        root = Ito(s, 1, -1)
        
        itor_r = arborform.Reflect()

        # Add
        itor_tok_split = Itorator.wrap(lambda ito: ito.str_split())
        con = Connectors.Children.Add(itor_tok_split)
        itor_r.connections.append(con)

        with self.subTest(children_type=type(con).__name__):
            rv = [*itor_r(root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(len(root.str_split()), len(rv[0].children))

        all_tokens_root = rv[0]

        # AddHierarchical
        itor_char_split = Itorator.wrap(lambda ito: itertools.chain.from_iterable(ito.children))
        con = Connectors.Children.AddHierarchical(itor_char_split)
        itor_r.connections.clear()
        itor_r.connections.append(con)

        with self.subTest(children_type=type(con).__name__):
            rv = [*itor_r(all_tokens_root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(len(root.str_split()), len(rv[0].children))
            for t in rv[0].children:
                self.assertEqual(len(t), len(t.children))

        # Delete
        def numerics(ito) -> Types.C_IT_ITOS:
            for c in ito.children:
                if c.str_isnumeric():
                    yield c
        itor_numerics = Itorator.wrap(numerics)
        con = Connectors.Children.Delete(itor_numerics)
        itor_r.connections.clear()
        itor_r.connections.append(con)
        
        with self.subTest(children_type=type(con).__name__):
            rv = [*itor_r(all_tokens_root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(sum(1 for i in all_tokens_root.children if i.str_isnumeric()), len(rv[0].children))

        # Replace
        def alphas(ito) -> Types.C_IT_ITOS:
            for c in ito.children:
                if not c.str_isnumeric():
                    c.desc = 'alpha'
                    yield c
        itor_alphas = Itorator.wrap(alphas)
        con = Connectors.Children.Replace(itor_alphas)
        itor_r.connections.clear()
        itor_r.connections.append(con)

        with self.subTest(children_type=type(con).__name__):
            rv = [*itor_r(all_tokens_root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(sum(1 for i in all_tokens_root.children if not i.str_isnumeric()), len(rv[0].children))
            self.assertTrue(all(i.desc == 'alpha' for i in rv[0].children))
            
        with self.subTest(children_type=type(con).__name__):
            rv = [*itor_r(all_tokens_root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(sum(1 for i in all_tokens_root.children if i.str_isnumeric()), len(rv[0].children))

        itor_alphas = Itorator.wrap(alphas)
        con = Connectors.Children.Replace(itor_alphas)
        itor_r.connections.clear()
        itor_r.connections.append(con)

        with self.subTest(children_type=type(con).__name__):
            rv = [*itor_r(all_tokens_root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(sum(1 for i in all_tokens_root.children if not i.str_isnumeric()), len(rv[0].children))
            self.assertTrue(all(i.desc == 'alpha' for i in rv[0].children))

    def test_traverse_complex(self):
        s = ' one two three '
        root = Ito(s, 1, -1)
        
        itor_wrd_split = Itorator.wrap(lambda ito: ito.str_split())

        itor_wrd_desc = Itorator.wrap(lambda ito: [ito.clone(desc='word'), ])
        con = Connectors.Recurse(itor_wrd_desc)
        itor_wrd_split.connections.append(con)

        itor_char_split = Itorator.wrap(lambda ito: ito)
        con = Connectors.Children.Add(itor_char_split)
        itor_wrd_split.connections.append(con)

        itor_char_desc = Itorator.wrap(lambda ito: [ito.clone(desc='char'), ])
        con = Connectors.Recurse(itor_char_desc)
        itor_char_split.connections.append(con)

        itor_char_desc_vowel = Itorator.wrap(lambda ito: [ito.clone(desc='char-vowel'), ])
        con = Connectors.Recurse(itor_char_desc_vowel, lambda ito: str(ito) in 'aeiou')
        itor_char_desc.connections.append(con)

        rv = [*itor_wrd_split(root)]

        self.assertSequenceEqual(root.split(regex.compile(r'\s+'), desc='word'), rv)
        for word in rv:
            self.assertEqual(len(word), len(word.children))
            for c in word.children:
                if str(c) in 'aeiou':
                    self.assertEqual('char-vowel', c.desc)
                else:
                    self.assertEqual('char', c.desc)
