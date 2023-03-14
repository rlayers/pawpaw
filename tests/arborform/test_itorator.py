import itertools
import typing

import regex
from pawpaw import Ito, Types
from pawpaw.arborform import Itorator, Connectors, Postorator
from tests.util import _TestIto


class TestItorator(_TestIto):
    @classmethod
    def get_reflect(cls) -> Itorator:
        return Itorator.wrap(lambda ito: (ito,))

    @classmethod
    def change_desc(cls, ito: Ito, desc: str | None) -> Types.C_IT_ITOS:
        ito.desc = desc
        return ito,

    @classmethod
    def get_desc(cls, desc: str | None) -> Itorator:
        return Itorator.wrap(lambda ito: cls.change_desc(ito, desc))

    def test_call_fails_on_non_ito(self):
        s = ' abc '
        itor = self.get_reflect()
        with self.assertRaises(TypeError):
            next(itor(s))

    def test_call_clones_ito(self):
        s = ' abc '
        root = Ito(s, 1, -1)
        itor = self.get_reflect()
        rv = next(itor(root))
        self.assertEqual(root, rv)
        self.assertIsNot(root, rv)

    def test_traverse_does_not_clone(self):
        s = ' abc '
        root = Ito(s, 1, -1)
        itor = self.get_reflect()
        rv = next(itor._traverse(root))
        self.assertIs(root, rv)

    def test_wrap(self):
        s = ' abc '
        root = Ito(s, 1, -1)
        desc = 'x'
        itor = self.get_desc(desc)
        rv = next(itor(root))
        self.assertNotEqual(desc, root.desc)
        self.assertEqual(desc, rv.desc)

    def test_clone(self):
        s = ' abc '
        root = Ito(s, 1, -1)
        tag = 'x'
        itor_r = self.get_reflect()
        itor_r.tag = tag

        itor_d = self.get_desc('foo')
        con = Connectors.Delegate(itor_d)
        itor_r.connections.append(con)

        self.assertEqual(tag, itor_r.tag)
        self.assertEqual(1, len(itor_r.connections))

        itor_c = itor_r.clone()
        self.assertIsNot(itor_r, itor_c)
        self.assertEqual(tag, itor_c.tag)
        self.assertEqual(0, len(itor_c.connections))

    #region Connectors

    def test_yield_break_1(self):
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

    def test_yield_break_2(self):
        s = ' abc '
        root = Ito(s, 1, -1)
        desc = 'x'
        itor_r = self.get_reflect()
        itor_d = self.get_desc(desc)

        lambdas = {
            '[default]': None,
            'Always True': lambda ito: True,
            'Always False': lambda ito: False,
        }

        for lam_desc, lam_f in lambdas.items():
            with self.subTest(lambda_=lam_desc):
                if lam_f is None:
                    itor_r.connections.append(Connectors.Delegate(itor_d))
                else:
                    itor_r.connections.append(Connectors.Delegate(itor_d, lam_f))

                if lam_f is None or lam_f(root):
                    expected = self.change_desc(root, desc)[0]
                else:
                    expected = root

                rv = next(itor_r(root))
                self.assertEqual(expected, rv)

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

    def test_assign_with_pipeline(self):
        s = ' one 123 two 456 '
        root = Ito(s, 1, -1)

        itor_r = self.get_reflect()

        # create sub-pipeline with two endpoints
        itor_tok_split = Itorator.wrap(lambda ito: ito.str_split())
        con = Connectors.Recurse(itor_tok_split)
        itor_r.connections.append(con)

        itor_desc_word = self.get_desc('word')
        con = Connectors.Delegate(itor_desc_word, lambda ito: not ito.str_isnumeric())
        itor_tok_split.connections.append(con)

        itor_desc_num = self.get_desc('number')
        con = Connectors.Delegate(itor_desc_num)
        itor_tok_split.connections.append(con)

        # ensure this works as expected
        rv = [*itor_r(root)]
        self.assertEqual(len(root.str_split()), len(rv))
        self.assertTrue(all(i.desc in ['word', 'number'] for i in rv))

        # now add a Next connection AFTER the sub-pipeline
        def prepend_x(ito) -> Types.C_IT_ITOS:
            ito.desc = 'x' + ito.desc
            return ito,

        itor_desc_pre_x = Itorator.wrap(prepend_x)
        con = Connectors.Delegate(itor_desc_pre_x)
        itor_r.connections.append(con)

        # ensure next connects to all the sub-pipeline's endpoints
        rv = [*itor_r(root)]
        self.assertEqual(len(root.str_split()), len(rv))
        self.assertTrue(all(i.desc.startswith('x') for i in rv))

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
        rv = [*itor_1(root)]

        self.assertSequenceEqual([Ito(root, 1, -1, 'x')], rv)

    def test_children(self):
        s = ' one 123 two 456 '
        root = Ito(s, 1, -1)
        
        itor_r = self.get_reflect()

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

    def test_postorator(self):
        s = 'abc def ghi'
        root = Ito(s)

        def simple_join(itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
            yield Ito.join(*itos)

        word_splitter = Itorator.wrap(lambda ito: ito.str_split())

        with self.subTest(chain_length=1, chain_depth=0):
            rv = [*word_splitter(root)]
            self.assertSequenceEqual(root.str_split(), rv)

            word_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*word_splitter(root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(root, rv[0])

        with self.subTest(chain_length=2, chain_depth=0):
            word_splitter = word_splitter.clone()

            char_splitter = Itorator.wrap(lambda ito: ito)
            con = Connectors.Delegate(char_splitter)
            word_splitter.connections.append(con)
            expected = [j for i in word_splitter(root) for j in i]
            rv = [*word_splitter(root)]
            self.assertSequenceEqual(expected, rv)

            word_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*word_splitter(root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(root, rv[0])

            word_splitter.postorator = None
            char_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*word_splitter(root)]
            self.assertSequenceEqual(root.str_split(), rv)

        with self.subTest(chain_length=1, chain_depth=1):
            word_splitter = word_splitter.clone()
            char_splitter = char_splitter.clone()

            con = Connectors.Children.Add(char_splitter)
            word_splitter.connections.append(con)
            rv = [*word_splitter(root)]
            self.assertSequenceEqual(root.str_split(), rv)
            for w in rv:
                self.assertSequenceEqual([*w], [*w.children])

            word_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*word_splitter(root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(root, rv[0])

            word_splitter.postorator = None
            char_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*word_splitter(root)]
            self.assertSequenceEqual(root.str_split(), rv)
            for w in rv:
                self.assertSequenceEqual([w,], [*w.children])

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

    #endregion