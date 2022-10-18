import typing

import regex
from segments import Ito
import segments
from tests.util import _TestIto


class TestItoQuery(_TestIto):
    def setUp(self) -> None:
        super().setUp()

        self.src = 'nine 9 ten 10 eleven 11 TWELVE 12 thirteen 13'
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)(?: |$))+')
        
        self.root = Ito(self.src, self.src.index('ten'), self.src.index('thirteen') - 1, desc='root')
        self.root.children.add(*Ito.from_re(re, self.root))
        self.leaves = [d for d in self.root.walk_descendants() if len(d.children) == 0]
        self.leaf = next(i for i in self.leaves if i.parent.__str__() == 'eleven' and i.__str__() == 'v')
                                                                        
        self.descs = ['root', 'phrase', 'word', 'char']

    # region axis

    def test_axis_root(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'....{order}'
                with self.subTest(node=node_type, query=query):
                    i = node.find(query)
                    self.assertIs(self.root, i)

    def test_axis_ancestors(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'...{order}'
                with self.subTest(node=node_type, query=query):
                    expected = self.descs[:self.descs.index(node.desc)]
                    if order != 'r':
                        expected.reverse()
                    actual = [*node.find_all(query)]
                    self.assertSequenceEqual(expected, [a.desc for a in actual])
                    for e, a in zip(expected, actual):
                        self.assertEqual(e, a.desc)

    def test_axis_parent(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'..{order}'
                with self.subTest(node=node_type, query=query):
                    i = node.find(query)
                    self.assertIs(node.parent, i)

    def test_axis_self(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'.{order}'
                with self.subTest(node=node_type, query=query):
                    i = node.find(query)
                    self.assertIs(node, i)

    def test_axis_dedup(self):
        # First ensure dups present
        query = f'*/..'
        rv = [*self.root.find_all(query)]
        self.assertEqual(len(self.root.children), len(rv))
        self.assertTrue(all(i is self.root for i in rv))
                                                                        
        # Now make sure they get removed
        for order in '', 'n', 'r':
            query = f'*/../-{order}'
            with self.subTest(query=query):
                rv = [*self.root.find_all(query)]
                self.assertEqual(1, len(rv))
                self.assertIs(self.root, rv[0])
                                                                        
    def test_axis_children(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'*{order}'
                with self.subTest(node=node_type, query=query):
                    expected = [*node.children]
                    if order == 'r':
                        expected.reverse()
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)

    def test_axis_descendants(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'**{order}'
                with self.subTest(node=node_type, query=query):
                    expected = [*node.walk_descendants()]
                    if order == 'r':
                        expected.reverse()
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)

    def test_axis_leaves(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'***{order}'
                with self.subTest(node=node_type, query=query):
                    expected = self.leaves if node is self.root else []
                    if order == 'r':
                        expected.reverse()
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)

    def test_prior_siblings(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'<<{order}'
                with self.subTest(node=node_type, query=query):
                    if node.parent is None:
                        expected: typing.List[Ito] = []
                    else:
                        i = node.parent.children.index(node)
                        expected = node.parent.children[:i]
                    if order == 'r':
                        expected.reverse()
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)

    def test_prior_sibling(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'<{order}'
                with self.subTest(node=node_type, query=query):
                    if node.parent is None:
                        expected: typing.List[Ito] = []
                    else:
                        i = node.parent.children.index(node)
                        expected = node.parent.children[i-1:i]
                    if order == 'r':
                        expected.reverse()
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)

    def test_next_sibling(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'>{order}'
                with self.subTest(node=node_type, query=query):
                    if node.parent is None:
                        expected: typing.List[Ito] = []
                    else:
                        i = node.parent.children.index(node)
                        expected = node.parent.children[i + 1:i + 2]
                    if order == 'r':
                        expected.reverse()
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)

    def test_next_siblings(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', 'n', 'r':
                query = f'>>{order}'
                with self.subTest(node=node_type, query=query):
                    if node.parent is None:
                        expected: typing.List[Ito] = []
                    else:
                        i = node.parent.children.index(node)
                        expected = node.parent.children[i + 1:]
                    if order == 'r':
                        expected.reverse()
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)

    # endregion
    
    # region filter
    
    # region filter desc
    
    def test_filter_desc_scalar(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for desc in 'word', 'char':
                query = f'**[d:{desc}]'
                with self.subTest(node=node_type, query=query):
                    expected = [d for d in node.walk_descendants() if d.desc == desc]
                    actual = [*node.find_all(query)]
                    self.assertSequenceEqual(expected, actual)
    
    def test_filter_desc_multiple(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            descs = 'word', 'char'
            query = f'**[d:{",".join(descs)}]'
            with self.subTest(node=node_type, query=query):
                expected = [d for d in node.walk_descendants() if d.desc in descs]
                actual = [*node.find_all(query)]
                self.assertSequenceEqual(expected, actual)

    # endregion
    
    # region filter string
    
    def test_filter_string_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for s in 'ten', 'eleven', 'twelve':
                query = f'**[s:{segments.query.escape(s)}]'
                with self.subTest(node=node_type, query=query):
                    expected = [d for d in node.walk_descendants() if d.__str__() == s]
                    actual = [*node.find_all(query)]
                    self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_multiple(self):
        for node_type, node in {'root': self.root}.items():
            strings = 'ten', 'eleven', 'twelve'
            query = f'**[s:{",".join(segments.query.escape(s) for s in strings)}]'
            with self.subTest(node=node_type, query=query):
                expected = [d for d in node.walk_descendants() if d.__str__() in strings]
                actual = [*node.find_all(query)]
                self.assertSequenceEqual(expected, actual)
    
    # endregion
    
    # region filter string casefold
    
    def test_filter_string_casefold_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for s in 'ten', 'ELEVEN', 'twelve':
                for case_func in str.upper, str.casefold, str.lower:
                    s = case_func(s)
                    query = f'**[scf:{segments.query.escape(s)}]'
                    with self.subTest(node=node_type, query=query):
                        expected = [d for d in node.walk_descendants() if d.__str__().casefold() == s.casefold()]
                        actual = [*node.find_all(query)]
                        self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_casefold_multiple(self):
        for node_type, node in {'root': self.root}.items():
            basis = 'ten', 'ELEVEN', 'twelve'
            for case_func in str.upper, str.casefold, str.lower:
                cfs = [case_func(s) for s in basis]
                query = f'**[scf:{",".join(segments.query.escape(s) for s in cfs)}]'
                with self.subTest(node=node_type, query=query):
                        expected = [d for d in node.walk_descendants() if d.__str__().casefold() in [s.casefold() for s in cfs]]
                        actual = [*node.find_all(query)]
                        self.assertSequenceEqual(expected, actual)
    
    # endregion

    # region filter index
                
    def test_filter_index_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', 'r':
                for index in 0, 1, 2:
                    query = f'*{order}[i:{index}]'
                    with self.subTest(node=node_type, order=order, index=index, query=query):
                        expected = [c for c in node.children]
                        if order == 'r':
                            expected.reverse()
                        expected = [expected[index]]
                        actual = [*node.find_all(query)]
                        self.assertSequenceEqual(expected, actual)
                
    def test_filter_index_range(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', 'r':
                for index in (0, 1), (1, 2), (0, 2):
                    istr = '-'.join(str(i) for i in index)
                    query = f'*{order}[i:{istr}]'
                    with self.subTest(node=node_type, order=order, index=istr, query=query):
                        expected = [c for c in node.children]
                        if order == 'r':
                            expected.reverse()
                        expected = expected[slice(*index)]
                        actual = [*node.find_all(query)]
                        self.assertSequenceEqual(expected, actual)

    def test_filter_index_mix(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', 'r':
                for istr, _slices in (('0,2-4,6', (slice(0, 1), slice(2, 4), slice(6, 7))), ):
                    query = f'**{order}[i:{istr}]'
                    with self.subTest(node=node_type, order=order, index=istr, query=query):
                        tmp = [*node.walk_descendants()]
                        if order == 'r':
                            tmp.reverse()
                        expected = []
                        for _slice in _slices:
                            expected.extend(tmp[_slice])
                        actual = [*node.find_all(query)]
                        self.assertSequenceEqual(expected, actual)

    # endregion
    
    # region filter predicate
    
    # TODO : Add filter predicates test(s)
    
    # endregion
    
    # TODO : Add filter values test(s)

    # region filter value
    
    # endregion

    # region subquery
    
    def test_subquery_scalar(self):
        for node_type, node in {'root': self.root}.items()
            for order in '', 'r':
                query = '**' + order + '[d:word]{*[d:char]&[s:e]}'  # words with 'e'
                with self.subTest(node=node_type, order=order, query=query):
                    step = -1 if order == 'r' else 1
                    expected = [*dict.fromkeys(leaf.parent for leaf in self.leaves[::step] if leaf.__str__() == 'e').keys()]
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)
    
    # endregion
