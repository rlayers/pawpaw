import typing

import regex
from pawpaw import Ito, Types
from pawpaw.arborform import Itorator, Reflect
from tests.util import _TestIto


class TestItorator(_TestIto):
    """Uses Reflect and Wrap classes, which have trivial implementation, to test base class functionality"""

    def test_add_self(self):
        i = Reflect()

        with self.assertRaises(ValueError):
            i.itor_children = i

        with self.assertRaises(ValueError):
            i.itor_next = i

    def test_wrap_lambda(self):
        s = 'abc'
        root = Ito(s)
        itor = Itorator.wrap(lambda ito: [ito[:1]])
        self.assertListEqual([root[:1]], [*itor.traverse(root)])

    def test_wrap_method(self):
        def my_split(ito: Ito) -> Types.C_SQ_ITOS:
            yield from ito.str_split()

        s = 'one two three'
        root = Ito(s)
        itor = Itorator.wrap(my_split)
        self.assertListEqual([*Ito.from_substrings(s, s.split())], [*itor.traverse(root)])

    def test_wrap_itorator(self):
        # Create itorator with two end points
        itor_split_words = Itorator.wrap(lambda ito: ito.str_split())
        itor_strip_first = Itorator.wrap(lambda ito: [ito[1:]])
        itor_strip_last = Itorator.wrap(lambda ito: [ito[:-1]])
        itor_split_words.itor_next = lambda ito: itor_strip_first if str(ito) == 'two' else itor_strip_last

        # Wrap the multi-endpoint itorator
        itor_wrap = Itorator.wrap(itor_split_words)

        # Attach successor to wrapped
        itor_split_chars = Itorator.wrap(lambda ito: [i for i in ito])
        itor_wrap.itor_next = itor_split_chars

        s = 'one two three'
        root = Ito(s)
        self.assertListEqual(['o', 'n', 'w', 'o', 't', 'h', 'r', 'e'], [str(i) for i in itor_wrap.traverse(root)])

    def test_traverse(self):
        s = 'abc'
        root = Ito(s)
        self.add_chars_as_children(root, 'Child')

        reflect = Reflect()
        rv = [*reflect.traverse(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertEqual(root, ito)
        self.assertEqual([*root.children], [*ito.children])

    def test_traverse_with_next(self):
        s = 'abc'
        root = Ito(s)
        self.add_chars_as_children(root, 'Child')

        reflect = Reflect()
        desc = 'x'
        reflect.itor_next = Itorator.wrap(lambda ito: (ito.clone(desc=desc),))
        rv = [*reflect.traverse(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertEqual(desc, ito.desc)
        self.assertEqual([*root.children], [*ito.children])

    def test_traverse_with_children(self):
        s = 'abc'
        root = Ito(s)

        reflect = Reflect()
        desc = 'x'
        reflect.itor_children = Itorator.wrap(lambda ito: tuple(ito.clone(i, i+1, desc) for i, c in enumerate(s)))
        rv = [*reflect.traverse(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertSequenceEqual(s, [str(i) for i in ito.children])
        self.assertTrue(all(c.desc == desc for c in ito.children))
        
    def test_traverse_with_carry_through(self):
        s = 'abc'
        root = Ito(s)
        d_changed = 'changed'

        reflect = Reflect()
        make_chars = Itorator.wrap(lambda ito: tuple(ito.clone(i, i+1, 'char') for i in range(*ito.span)))
        reflect.itor_children = make_chars
        rename = Itorator.wrap(lambda ito: tuple(ito.clone(desc=d_changed) if i.parent is not None else i for i in [ito]))
        make_chars.itor_next = rename
        rv = [*reflect.traverse(root)]
            
        self.assertEqual(1, len(rv))
        ito = rv[0]
        self.assertIsNot(root, ito)
        self.assertSequenceEqual(s, [str(i) for i in ito.children])
        self.assertTrue(all(c.desc == d_changed for c in ito.children))

    def test_traverse_with_post_processor(self):
        s = 'abc def ghi'
        root = Ito(s)

        reflect = Reflect()

        word_splitter = Itorator.wrap(lambda ito: ito.str_split())
        reflect.itor_next = word_splitter

        char_splitter = Itorator.wrap(lambda ito: [*ito])

        def simple_join(itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
            window = list(itos)
            yield from (Types.C_BITO(False, i) for i in window)
            yield Types.C_BITO(True, Ito.join(*window))

        with self.subTest(chain_length=1, scenario='itor_next'):
            rv = [*reflect.traverse(root)]
            self.assertEqual(3, len(rv))

            word_splitter.postorator = simple_join
            rv = [*reflect.traverse(root)]
            self.assertEqual(1, len(rv))

        with self.subTest(chain_length=2, scenario='itor_next'):
            word_splitter.postorator = None
            word_splitter.itor_next = char_splitter
            rv = [*reflect.traverse(root)]
            self.assertEqual(9, len(rv))

            char_splitter.postorator = simple_join
            rv = [*reflect.traverse(root)]
            self.assertEqual(3, len(rv))

            word_splitter.postorator = simple_join
            rv = [*reflect.traverse(root)]
            self.assertEqual(1, len(rv))

            char_splitter.postorator = None
            rv = [*reflect.traverse(root)]
            self.assertEqual(1, len(rv))

        with self.subTest(chain_length=2, scenario='itor_child'):
            word_splitter.postorator = None
            word_splitter.itor_next = None
            word_splitter.itor_children = char_splitter
            rv = [*reflect.traverse(root)]
            self.assertEqual(3, len(rv))
            self.assertEqual(9, sum(len(i.children) for i in rv))            

            char_splitter.postorator = simple_join
            rv = [*reflect.traverse(root)]
            self.assertEqual(3, len(rv))
            self.assertEqual(3, sum(len(i.children) for i in rv))            

            word_splitter.postorator = simple_join
            rv = [*reflect.traverse(root)]
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
        
        namer.itor_children = lambda ito: splt_digits if ito.desc == 'numeric' else splt_case
        
        func = lambda ito: [ito.clone(i, i + 1, desc='char') for i in range(ito.start, ito.stop)]
        splt_chars = Itorator.wrap(func)
        splt_case.itor_children = splt_chars
        
        root.children.add(*splt_space.traverse(root))
        
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
