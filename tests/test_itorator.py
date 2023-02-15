import typing

import regex
from pawpaw import Ito, Types, PredicatedValue
from pawpaw.arborform import Itorator, Postorator, Reflect, Desc
from tests.util import _TestIto


class TestItorator(_TestIto):
    """Uses Reflect and Wrap classes, which have trivial implementation, to test base class functionality"""

    def test_add_self_itor_sub(self):
        i1 = Reflect()

        for itor in i1, Reflect():
            with self.subTest(itor_is_self=itor is i1):
                i1.itor_sub = itor
                self.assertEqual(1, len(i1.itor_sub))
                self.assertEqual(itor, i1.itor_sub[0].value)
                
                i1.itor_sub = None
                self.assertEqual(0, len(i1.itor_sub))

    def test_add_self_itor_children(self):
        i1 = Reflect()

        for itor in i1, Reflect():
            with self.subTest(itor_is_self=itor is i1):
                i1.itor_children = itor
                self.assertEqual(1, len(i1.itor_children))
                self.assertEqual(itor, i1.itor_children[0].value)
                
                i1.itor_children = None
                self.assertEqual(0, len(i1.itor_children))

    def test_add_self_itor_next(self):
        i1 = Reflect()

        for itor in i1, Reflect():
            with self.subTest(itor_is_self=itor is i1):
                i1.itor_next = itor
                self.assertEqual(1, len(i1.itor_next))
                self.assertEqual(itor, i1.itor_next[0].value)
                
                i1.itor_next = None
                self.assertEqual(0, len(i1.itor_next))                

    def test_update_itor_children_mode_valid(self):
        itor = Reflect()

        # Loop twice in case the initial set is the default value
        for i in range(2):
            for icm in Itorator.ItorChildrenMode:
                itor.itor_children_mode = icm
                self.assertEqual(icm, itor.itor_children_mode)

    def test_update_itor_children_mode_ivalid(self):
        itor = Reflect()

        with self.assertRaises(TypeError):
            itor.itor_children_mode = 'a'

        with self.assertRaises(TypeError):
            itor.itor_children_mode = None

    def test_wrap_lambda(self):
        s = 'abc'
        root = Ito(s)
        itor = Itorator.wrap(lambda ito: [ito[:1]])
        self.assertSequenceEqual(root[:1], [*itor(root)])

    def test_wrap_method(self):
        def my_split(ito: Ito) -> Types.C_SQ_ITOS:
            yield from ito.str_split()

        s = 'one two three'
        root = Ito(s)
        itor = Itorator.wrap(my_split)
        self.assertSequenceEqual([*Ito.from_substrings(s, *s.split())], [*itor(root)])

    def test_traverse_clones(self):
        s = 'abc'
        root = Ito(s)
        reflect = Reflect()
        rv = [*reflect(root)]
        self.assertEqual(1, len(rv))
        self.assertEqual(root, rv[0])
        self.assertIsNot(root, rv[0])

    def test_traverse_does_clone(self):
        s = 'abc'
        root = Ito(s)
        root.children.add(*root)

        reflect = Reflect()
        rv = [*reflect(root)]
            
        self.assertEqual(1, len(rv))
        self.assertEqual(root, rv[0])
        self.assertIsNot(root, rv[0])

        self.assertSequenceEqual([*root.children], [*rv[0].children])
        self.assertTrue(root_c is not rv_c for root_c, rv_c in zip(root.children, rv[0].children))

    def test_traverse_with_itor_sub(self):
        s = 'abc'
        root = Ito(s)

        itor_root = Reflect()
        itor_root.itor_sub = Itorator.wrap(lambda ito: (Ito(ito, 1, -1),))
        rv = [*itor_root(root)]
            
        self.assertEqual(1, len(rv))
        self.assertNotEqual(root, rv[0])
        self.assertSequenceEqual([*root.children], [*rv[0].children])

    def test_traverse_with_itor_children_mode_add(self):
        s = 'abc'
        root = Ito(s)

        itor_root = Reflect()
        itor_root.itor_children = Itorator.wrap(lambda ito: ito)
        rv = [*itor_root(root)]
            
        self.assertEqual(1, len(rv))
        self.assertEqual(str(root), str(rv[0]))

        self.assertEqual(0, len(root.children))  # Ensure input ito.children unaffected
        self.assertSequenceEqual(root, rv[0].children)

    def test_traverse_with_itor_children_mode_replace_with_self(self):
        s = 'a b c'
        root = Ito(s)
        root.children.add(*root)

        itor_root = Reflect()

        itor_children = lambda ito: ito.children
        itor_root.itor_children = itor_children
        itor_root.itor_children_mode = Itorator.ItorChildrenMode.REPLACE

        rv = [*itor_root(root)]
            
        self.assertEqual(1, len(rv))
        self.assertEqual(str(root), str(rv[0]))

        self.assertSequenceEqual([*root.children], [*rv[0].children])

    def test_traverse_with_itor_children_mode_replace_with_clones(self):
        s = 'a b c'
        root = Ito(s)
        root.children.add(*root)

        itor_root = Reflect()

        itor_children = lambda ito: [c.clone() for c in ito.children]
        itor_root.itor_children = itor_children
        itor_root.itor_children_mode = Itorator.ItorChildrenMode.REPLACE

        rv = [*itor_root(root)]
            
        self.assertEqual(1, len(rv))
        self.assertEqual(str(root), str(rv[0]))

        self.assertSequenceEqual([*root.children], [*rv[0].children])        

    def test_traverse_with_itor_children_mode_replace_with_different(self):
        s = 'a b c'
        root = Ito(s)
        root.children.add(*root)

        f = lambda ito: (Ito(ito, 1, -1),)

        itor_root = Reflect()
        itor_root.itor_children = Itorator.wrap(f)
        itor_root.itor_children_mode = Itorator.ItorChildrenMode.REPLACE
        rv = [*itor_root(root)]
            
        self.assertEqual(1, len(rv))
        self.assertEqual(str(root), str(rv[0]))

        self.assertNotEqual(len(root.children), len(rv[0].children))
        self.assertEqual(1, len(rv[0].children))
        
        self.assertSequenceEqual([*f(root)], [*rv[0].children])        

    def test_traverse_with_itor_children_mode_delete(self):
        s = 'a b c'
        root = Ito(s)
        root.children.add(*root)

        f = lambda ito: ito.children[1:-1]

        itor_root = Reflect()
        itor_root.itor_children = Itorator.wrap(f)
        itor_root.itor_children_mode = Itorator.ItorChildrenMode.DEL
        rv = [*itor_root(root)]
            
        self.assertEqual(1, len(rv))
        self.assertEqual(str(root), str(rv[0]))

        self.assertNotEqual(len(root.children), len(rv[0].children))
        self.assertEqual(2, len(rv[0].children))
        
        expected = list(set(root.children) - set(f(root)))
        self.assertSequenceEqual(expected, [*rv[0].children])    
        
    def test_traverse_with_plumule_on_added_children(self):
        s = ' one two three '
        root = Ito(s, 1, -1)

        expected = root.clone()
        expected.children.add(*expected.str_split())
        for c in expected.children:
            c.children.add(*c)

        itor_split_wrds = Itorator.wrap(lambda ito: ito.str_split())

        itor_split_chrs = Itorator.wrap(lambda ito: ito)
        itor_split_wrds.itor_children = itor_split_chrs

        itor_word_desc = Desc('word')
        itor_split_wrds.itor_next = lambda ito: ito.find('*') is not None, itor_word_desc  # plumule child search

        itor_children = Itorator.wrap(lambda ito: ito.children)
        itor_word_desc.itor_children_mode = Itorator.ItorChildrenMode.REPLACE
        itor_word_desc.itor_children = itor_children

        itor_chr_desc = Desc('char')
        itor_children.itor_next = lambda ito: ito.find('..') is not None, itor_chr_desc  # plumule parent search

        rv = root.clone()
        rv.children.add(*itor_split_wrds(root))

        self.assertSequenceEqual(
            [str(i) for i in expected.find_all('**')],
            [str(i) for i in rv.find_all('**')]
        )

        for child in rv.children:
            self.assertEqual('word', child.desc)
            for gc in child.children:
                self.assertEqual('char', gc.desc)

    def test_traverse_with_itor_next(self):
        s = 'abc'
        root = Ito(s)

        itor_root = Reflect()
        itor_root.itor_next = Itorator.wrap(lambda ito: (Ito(ito, 1, -1),))
        rv = [*itor_root(root)]
            
        self.assertEqual(1, len(rv))
        self.assertNotEqual(root, rv[0])
        self.assertSequenceEqual([*root.children], [*rv[0].children])
        
    def test_traverse_with_carry_through(self):
        s = 'abc'
        root = Ito(s)
        d_changed = 'changed'

        reflect = Reflect()
        make_chars = Itorator.wrap(lambda ito: tuple(ito.clone(i, i+1, 'char') for i in range(*ito.span)))
        reflect.itor_children = make_chars
        rename = Itorator.wrap(lambda ito: (ito.clone(desc=d_changed),))
        make_chars.itor_next = rename
        rv = [*reflect(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertSequenceEqual(s, [str(i) for i in ito.children])
        self.assertTrue(all(c.desc == d_changed for c in ito.children))

    def test_traverse_with_sub(self):
        s = 'abcde'
        root = Ito(s)
        vowels = 'aeiou'

        chars = Itorator.wrap(lambda ito: [*ito])
        chars.itor_sub = lambda ito: str(ito) in vowels, Desc('vowel')
        chars.itor_sub.append(Desc('consonant'))

        results = [*chars(root)]
        self.assertEqual(len(s), len(results))
        self.assertListEqual([i for i in s if i in vowels], [str(i) for i in results if i.desc == 'vowel'])
        self.assertListEqual([i for i in s if i not in vowels], [str(i) for i in results if i.desc == 'consonant'])

        chars.itor_next = Desc('changed')
        results = [*chars(root)]
        self.assertEqual(len(s), len(results))
        self.assertTrue(all(i.desc == 'changed' for i in results))

    def test_traverse_with_postorator(self):
        s = 'abc def ghi'
        root = Ito(s)

        reflect = Reflect()

        word_splitter = Itorator.wrap(lambda ito: ito.str_split())
        reflect.itor_next = word_splitter

        char_splitter = Itorator.wrap(lambda ito: [*ito])

        def simple_join(itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
            yield Ito.join(*itos)

        with self.subTest(chain_length=1, scenario='itor_next'):
            rv = [*reflect(root)]
            self.assertEqual(3, len(rv))

            word_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*reflect(root)]
            self.assertEqual(1, len(rv))

        with self.subTest(chain_length=2, scenario='itor_next'):
            word_splitter.postorator = None
            word_splitter.itor_next = char_splitter
            rv = [*reflect(root)]
            self.assertEqual(9, len(rv))

            char_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*reflect(root)]
            self.assertEqual(3, len(rv))

            word_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*reflect(root)]
            self.assertEqual(1, len(rv))

            char_splitter.postorator = None
            rv = [*reflect(root)]
            self.assertEqual(1, len(rv))

        with self.subTest(chain_length=2, scenario='itor_child'):
            word_splitter.postorator = None
            word_splitter.itor_next = None
            word_splitter.itor_children = char_splitter
            rv = [*reflect(root)]
            self.assertEqual(3, len(rv))
            self.assertEqual(9, sum(len(i.children) for i in rv))            

            char_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*reflect(root)]
            self.assertEqual(3, len(rv))
            self.assertEqual(3, sum(len(i.children) for i in rv))            

            word_splitter.postorator = Postorator.wrap(simple_join)
            rv = [*reflect(root)]
            self.assertEqual(1, len(rv))
            self.assertEqual(0, len(rv[0].children))  # Ito.join doesn't include children

    def test_traverse_complex(self):
        basis = 'ABcd123'
        s = f' {basis} - {basis} '
        root = Ito(s, desc='root')
        
        func = lambda ito: [*ito.split(regex.compile(r'\-'), desc='phrase')]
        splt_space = Itorator.wrap(func)
        
        func = lambda ito: [ito.str_strip()]
        stripper = Itorator.wrap(func)
        splt_space.itor_children = stripper
        
        func = lambda ito: [*ito.split(regex.compile(r'(?<=[A-Za-z])(?=\d)'))]
        splt_alpha_num = Itorator.wrap(func)
        stripper.itor_children = splt_alpha_num
        
        func = lambda ito: [ito.clone(desc='numeric' if str(ito).isnumeric() else 'alpha')]
        namer = Itorator.wrap(func)
        splt_alpha_num.itor_next = namer
        
        func = lambda ito: [*ito.split(regex.compile(r'(?<=\d)(?=\d)'), desc='digit')]
        splt_digits = Itorator.wrap(func)
        
        func = lambda ito: [*ito.split(regex.compile(r'(?<=[A-Z])(?=[a-z])'), desc='upper or lower')]
        splt_case = Itorator.wrap(func)
        
        namer.itor_children = (lambda ito: ito.desc == 'numeric', splt_digits)
        namer.itor_children.append(splt_case)
        
        func = lambda ito: [ito.clone(i, i + 1, desc='char') for i in range(ito.start, ito.stop)]
        splt_chars = Itorator.wrap(func)
        splt_case.itor_children = splt_chars
        
        root.children.add(*splt_space(root))
        
        expected_child_count = s.count('-') + 1
        self.assertEqual(expected_child_count, len(root.children))
        
        expected_alpha_count = expected_child_count
        self.assertEqual(expected_alpha_count, sum(1 for i in root.find_all('**[d:alpha]')))
        
        expected_leaves_count = len(basis) * 2
        self.assertEqual(expected_leaves_count, sum(1 for i in root.find_all('***')))
            
        depth = 1
        cur = root
        while len(cur.children) > 0:
            cur = cur.children[0]
            depth += 1
        self.assertEqual(6, depth)
