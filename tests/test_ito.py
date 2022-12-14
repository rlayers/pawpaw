import itertools

import regex
from pawpaw import Span, Ito, nuco
from tests.util import _TestIto, IntIto


class TestIto(_TestIto):
    # region properties

    def test_string(self):
        s = 'abc'
        i = Ito(s)
        self.assertEqual(s, i.string)

    def test_span(self):
        s = 'abc'
        span = (1, 2)
        i = Ito(s, *span)
        self.assertEqual(span, i.span)

    def test_start(self):
        s = 'abc'
        span = Span(1, 2)
        i = Ito(s, *span)
        self.assertEqual(span.start, i.start)

    def test_stop(self):
        s = 'abc'
        span = Span(1, 2)
        i = Ito(s, *span)
        self.assertEqual(span.stop, i.stop)

    def test_set_parent_valid(self):
        s = 'abc'
        i1 = Ito(s)
        i2 = i1.clone(1, 2)
        i2._set_parent(i1)
        self.assertEqual(i1, i2.parent)

    def test_set_parent_invalid_parent(self):
        s = '__abc__'
        i1 = Ito(s, 1, -1)

        with self.subTest(scenario='different string'):
            i2 = Ito(s[1:])
            with self.assertRaises(ValueError):
                i2._set_parent(i1)

        with self.subTest(scenario='incompatible start'):
            i2 = Ito(s, stop=-1)
            with self.assertRaises(ValueError):
                i2._set_parent(i1)

        with self.subTest(scenario='incompatible stop'):
            i2 = Ito(s, 1)
            with self.assertRaises(ValueError):
                i2._set_parent(i1)

        with self.subTest(scenario='parent as self'):
            with self.assertRaises(ValueError):
                i1._set_parent(i1)

    def test_value_func(self):
        s = 'abc'
        ito = Ito(s)

        self.assertIsNone(ito.value_func)
        self.assertEqual(s, ito.value())

        f = lambda i: str(i) * 2
        ito.value_func = f
        self.assertEqual(f, ito.value_func)
        self.assertEqual(s * 2, ito.value())

        ito.value_func = None
        self.assertIsNone(ito.value_func)
        self.assertEqual(s, ito.value())

    def test_children(self):
        i = Ito('abc')
        self.assertIsNotNone(i.children)

    # endregion

    def test_value(self):
        f = lambda ito: int(str(ito))
        s = 'x123x'

        i = Ito(s, 1, -1)
        self.assertEqual(str(i), i.value())

        i.value_func = f
        self.assertEqual(i.value_func, f)
        self.assertEqual(f(str(i)), i.value())

        i.value_func = None
        self.assertIsNone(i.value_func)
        self.assertEqual(str(i), i.value())

    # region __x__ methods
    
    def test_eq_simple(self):
        s = 'abc'
        i1 = Ito(s, 1, -1, 'd')
        
        for s2 in '', i1.string:
            for start in None, i1.start:
                for stop in None, i1.stop:
                    for d in None, i1.desc:
                        i2 = Ito(s2, start, stop, d)
                        with self.subTest(first=i1, second=i2):
                            if i1.string == i2.string and i1.desc == i2.desc and i1.span == i2.span:
                                self.assertEqual(i1, i2)
                            else:
                                self.assertNotEqual(i1, i2)
                                
    def test_eq_derived(self):
        s = 'abc'
        i1 = Ito(s, 1, -1, 'd')
        i2 = IntIto(s, *i1.span, i1.desc)
        self.assertNotEqual(i1, i2)

    def test_eq_value_func(self):
        s = 'abc'
        f1 = lambda ito: str(ito).strip()
        f2 = lambda ito: str(ito).upper()
        
        # clone and ensure equal
        i1 = Ito(s, 1, -1, 'd')
        i2 = i1.clone()
        self.assertEqual(i1, i2)        

        # set second to something else and ensure nonequal
        i2.value_func = f1
        self.assertNotEqual(i1, i2)        

        # set first to same thing and ensure equal
        i1.value_func = f1
        self.assertEqual(i1, i2)        

        # set second to something else and ensure nonequal
        i2.value_func = f2
        self.assertNotEqual(i1, i2)        

        # set first to same thing and ensure equal
        i1.value_func = f2
        self.assertEqual(i1, i2)        

        # set second to None and ensure nonequal
        i2.value_func = None
        self.assertNotEqual(i1, i2)        
    
        # set first to None and ensure equal
        i1.value_func = None
        self.assertEqual(i1, i2)        

    def test_iter(self):
        s = ' abc '
        for span in Span.from_indices(s), Span.from_indices(s, 1, -1), Span.from_indices(s, 2, -2), Span(3, 3):
            with self.subTest(string=s, span=span):
                ito = Ito(s, *span)
                expected = [*Ito.from_substrings(s, s[slice(*span)])]
                actual = [*ito]
                self.assertListEqual(expected, actual)
                if len(actual) == 1:
                    self.assertIs(ito, actual[0])

    def test_iter_when_zero_length(self):
        # Ensure iter works the same for Ito as it does for str, i.e., it should yield nothing:
        #
        # >>> s = ''
        # >>> [*s]
        # []
        #

        ito = Ito('')
        self.assertListEqual([], [*ito])

    def test_repr(self):
        s = 'x123x'
        span = Span.from_indices(s, 1, -1)
        desc = 'd'
        for ito in Ito(s, *span, desc), IntIto(s, *span, desc):
            with self.subTest(string=s, ito=ito):
                expected = f'{type(ito).__name__}({s.__repr__()}, {span.start}, {span.stop}, {desc.__repr__()})'
                actual = ito.__repr__()
                self.assertEqual(expected, actual)
                self.assertEqual(ito, eval(actual))
    
    def test_str(self):
        s = 'x123x'
        for span in Span(0, len(s)), Span(1, len(s) - 1):
            for ito in Ito(s, *span), IntIto(s, *span):
                expected = s[slice(*span)]
                for expression in 'ito.__str__()', 'str(ito)', "f'{ito}'":
                    with self.subTest(string=s, ito=ito, expression=expression):
                        self.assertEqual(expected, eval(expression))

    def test_len(self):
        s = 'x123x'
        for span in Span(0, len(s)), Span(1, len(s) - 1):
            ito = Ito(s, *span)
            with self.subTest(string=s, ito=ito):
                expected = len(s[slice(*span)])
                self.assertEqual(expected, len(ito))
    
    def test_getitem_valid_int(self):
        s = 'x123x'
        ito = Ito(s, 1, -1)
        for i in range(-len(ito), len(ito)):
            with self.subTest(ito=ito, i=i):
                expected = str(ito)[i]
                actual = str(ito[i])
                self.assertEqual(expected, actual)
            
        s = 'x1x'
        ito = Ito(s, 1, -1)
        i = 0
        with self.subTest(ito=ito, i=i):
            self.assertIs(ito, ito[i])

    def test_getitem_invalid_int(self):
        s = 'x123x'
        ito = Ito(s, 1, -1)
        for i in None, '0':
            with self.subTest(ito=ito, i=i):
                with self.assertRaises(TypeError):
                    ito[i]

        for i in -100, -len(ito) - 1, len(ito), 100:
            with self.subTest(ito=ito, i=i):
                with self.assertRaises(IndexError):
                    ito[i]

    def test_getitem_valid_slice(self):
        s = 'x123x'
        ito = Ito(s, 1, -1)
        ito.children.add(*ito)
        for start in None, *range(-len(s) - 1, len(s) + 1):
            with self.subTest(ito=ito, start=start):
                span = Span.from_indices(ito, start).offset(ito.start)
                expected = ito.clone(*span, clone_children=False)
                actual = ito[start:]
                self.assertEqual(expected, actual)
                if ito == expected:
                    self.assertIs(ito, actual)
                for stop in None, *range(-len(s) - 1, len(s) + 1):
                    with self.subTest(ito=ito, start=start, stop=stop):
                        span = Span.from_indices(ito, start, stop).offset(ito.start)
                        expected = ito.clone(*span, clone_children=False)
                        actual = ito[start:stop]
                        self.assertEqual(expected, actual)
                        if ito == expected:
                            self.assertIs(ito, actual)
                        
    def test_getitem_invalid_slice(self):
        s = 'x123x'
        ito = Ito(s, 1, -1)
        for _slice in (slice(None, None, -1),):
            with self.subTest(ito=ito, slice=_slice):
                with self.assertRaises(IndexError):
                    ito[_slice]

    def test_format_directive(self):
        s = 'x123456789x'
        i = IntIto(s, 1, -1, 'my_desc')

        for directive in 'string', 'span', 'start', 'stop', 'desc', 'substr', 'value':
            with self.subTest(directive=directive):
                if directive == 'substr':
                    expected = str(i)
                elif directive == 'value':
                    expected = format(i.value(), 'n')
                else:
                    expected = getattr(i, directive)
                    if isinstance(expected, Span):
                        expected = str(tuple(expected))
                    elif not isinstance(expected, str):
                        expected = str(expected)
                actual = format(i, f'%{directive}')
                self.assertEqual(expected, actual)

    def test_format_int_directive(self):
        s = '0123456789' * 102
        i = IntIto(s, 1, -1, 'my_desc')

        for directive in 'span', 'start', 'stop':
            for fstr in ',', '10n', 'x>20,':
                with self.subTest(directive=directive, format_string=fstr):
                    if directive == 'span':
                        expected = f'({format(i.start, fstr)}, {format(i.stop, fstr)})'
                    elif directive == 'start':
                        expected = f'{format(i.start, fstr)}'
                    else:  # 'stop'
                        expected = f'{format(i.stop, fstr)}'
                    actual = format(i, f'%{directive}{":" + fstr}')
                    self.assertEqual(expected, actual)

    def test_format_str_conversion(self):
        s = ' \t\n\r '
        i = Ito(s, 1, -1, 'my_desc')

        for directive in 'string', 'substr':
            for conversion in '', 's', 'a', 'r':
                with self.subTest(directive=directive, conversion=conversion):
                    if directive == 'substr':
                        expected = str(i)
                    else:
                        expected = getattr(i, directive)
                    if conversion in ['', 's']:
                        pass
                    elif conversion == 'r':
                        expected = repr(expected)
                    else:
                        expected = ascii(expected)

                    if (conv := conversion) != '':
                        conv = '!' + conv
                    actual = format(i, f'%{directive}{conv}')
                    self.assertEqual(expected, actual)

    def test_format_str_width(self):
        s = ' Two\twords '
        i = Ito(s, 1, -1, 'my_desc')

        for directive in 'string', 'substr':
            for conversion in '', 'r':
                for width in 0, 1, 2, 3, 5, 10:
                    for suffix in '', '???', 'xx':
                        with self.subTest(directive=directive, conversion=conversion, width=width, suffix=suffix):
                            if directive == 'substr':
                                expected = str(i)
                            else:
                                expected = getattr(i, directive)

                            if conversion == 'r':
                                expected = repr(expected)

                            if len(expected) > width:
                                if (len_suf := len(suffix)) >= width:
                                    expected = suffix[len_suf - width:]
                                else:
                                    expected = expected[:width - len_suf] + suffix

                            f = f'%{directive}' \
                                f'{"!" + conversion if conversion != "" else ""}' \
                                f':{width}{suffix}'
                            actual = format(i, f)
                            self.assertEqual(expected, actual)

    # endregion

    # region combinatorics

    def test_adopt(self):
        s = 'abc 123'
        adopted_desc = 'adopted'

        children = [*Ito.from_substrings(s, s.split(), desc='children')]
        for child in children:
            child.children.add(*Ito.from_substrings(s, str(child), desc='grandchild'))
        grandchildren = [*itertools.chain.from_iterable(ito.children for ito in children)]

        adopted = Ito.adopt(children, desc=adopted_desc)
        self.assertTrue(all(adopted is not child for child in children))
        self.assertEqual(s, str(adopted))
        self.assertEqual(adopted_desc, adopted.desc)
        self.assertListEqual(grandchildren, [*adopted.children])
        
    def test_join(self):
        s = 'the quick brown fox'
        joined_desc = 'joined'
        children = [*Ito.from_substrings(s, s.split(), desc='children')]

        joined = Ito.join(children, desc=joined_desc)
        self.assertTrue(all(joined is not child for child in children))
        self.assertEqual(s, str(joined))
        self.assertEqual(joined_desc, joined.desc)

    def test_strip_to_children(self):
        basis = ' abc '
        ito = Ito(basis, 1, -1)
        s = basis[1:-1]
        with self.subTest(ito=ito, children_added=False):
            actual = ito.strip_to_children()
            self.assertIs(ito, actual)

        char_itos = [*Ito.from_substrings(basis, s)]
        for cs in char_itos[:1], char_itos[:2], char_itos[1:2], char_itos[1:], char_itos[2:], char_itos[:]:
            with self.subTest(ito=ito, children_added=False, children_strs=[str(i) for i in cs]):
                ito.children.add(*cs)
                actual = ito.strip_to_children()
                min_start = min(i.start for i in cs)
                max_stop = max(i.stop for i in cs)
                actual = ito.strip_to_children()
                if Span(min_start, max_stop) == ito.span:
                    self.assertIs(ito, actual)
                else:
                    self.assertEqual(min_start, actual.start)
                    self.assertEqual(max_stop, actual.stop)
                    self.assertSequenceEqual([*ito.children], [*actual.children])
                ito.children.clear()

    def test_invert_children(self):
        for s in '', 'AB', ' AB', 'A B', 'AB ', ' A B', 'A B ', ' A B ':
            parent = Ito(s)
            with self.subTest(string=s, children_added=False):
                inverted = parent.invert_children()
                expected = ''.join(str(c) for c in inverted.children)
                self.assertEqual(s, expected)

            parent.children.add(*parent.str_split())
            with self.subTest(string=s, children_added=True):
                inverted = parent.invert_children()
                clone = parent.clone(clone_children=False)
                clone.children.add(*(c.clone() for c in parent.children))
                clone.children.add(*(c.clone() for c in inverted.children))
                expected = ''.join(str(c) for c in clone.children)
                self.assertEqual(s, expected)
        
    def test_split_iter_simple(self):
        basis = 'A B C D E'
        for sep in ' ', '-':
            s = sep.join(basis.split())
            for padding in '', '=':
                s = f'{padding}{s}{padding}'
                ito = Ito(s, len(padding), len(s) - len(padding))
                for pattern in f'(?<={regex.escape(sep)})', regex.escape(sep), f'(?={regex.escape(sep)})':
                    re = regex.compile(pattern)
                    with self.subTest(string=s, separator=sep, pattern=pattern):
                        gaps = [Span(*m.span(0)).offset(-ito.start) for m in re.finditer(s, ito.start, ito.stop)]
                        expected = [*Ito.from_gaps(ito, *gaps)]
                        actual = [*ito.split_iter(re)]
                        self.assertListEqual(expected, actual)
                                
    def test_split_iter_sep_not_present(self):
        basis = 'A B C D E'
        for sep in ' ', '-':
            s = sep.join(basis.split())
            for padding in '', '=':
                s = f'{padding}{s}{padding}'
                ito = Ito(s, len(padding), len(s) - len(padding))
                pattern = r'XXX'
                re = regex.compile(pattern)
                with self.subTest(string=s, separator=sep, pattern=pattern):
                    expected = [ito]
                    actual = [*ito.split_iter(re)]
                    self.assertListEqual(expected, actual)
                    
    # endregion
