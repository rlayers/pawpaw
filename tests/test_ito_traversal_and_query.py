import typing

import regex
from segments import Ito
import segments
from tests.util import _TestIto


class TestItoQuery(_TestIto):
    def count_descdendants(cls, node: segments.Types.C_ITO) -> int:
        rv = len(node.children)
        for child in node.children:
            rv += cls.count_descdendants(child)
        return rv

    def setUp(self) -> None:
        super().setUp()

        self.src = 'nine 9 ten 10 eleven 11 TWELVE 12 thirteen 13'
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)(?: |$))+')
        
        self.root = Ito(self.src, self.src.index('ten'), self.src.index('thirteen') - 1, desc='root')
        self.root.children.add(*Ito.from_re(re, self.root))

        self.descendants_count = self.count_descdendants(self.root)

        numbers = [i for i in self.root.walk_descendants() if i.desc == 'number']
        for n in numbers:
            repl = self.IntIto(n, desc=n.desc)
            repl.children.add(*(self.IntIto(c, desc=c.desc) for c in n.children))
            p = n.parent
            i = p.children.index(n)
            p.children[i] = repl
        
        self.leaves = [d for d in self.root.walk_descendants() if len(d.children) == 0]
        
        self.leaf = next(i for i in self.leaves if str(i.parent) == 'eleven' and str(i) == 'v')
                                                                        
        self.descs = ['root', 'phrase', 'word', 'char']

    # region TRAVERSAL

    def test_walk_descendants(self):

        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for start in 0, 5:
                with self.subTest(node=node_type, start=start):
                    forward = [*node.walk_descendants_levels(start)]
                    _reversed = [*node.walk_descendants_levels(start, True)]

                    if node is self.root:
                        self.assertEqual(self.descendants_count, len(forward))
                        self.assertEqual(self.descendants_count, len(_reversed))
                    elif node is self.leaf:
                        self.assertEqual(0, len(forward))
                        self.assertEqual(0, len(_reversed))
                    if 0 < len(forward) == len(_reversed):
                        self.assertEqual(start, forward[0].index)
                        max_level = max(ei.index for ei in forward)
                        self.assertEqual(max_level, _reversed[0].index)

                    _reversed.reverse()
                    self.assertListEqual(forward, _reversed)

    # endregion

    # region QUERY

    # region axis

    def test_axis_root(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}....{or_self}'
                    with self.subTest(node=node_type, query=query):
                        i = node.find(query)
                        if node is not self.root or or_self == 'S':
                            self.assertIs(self.root, i)
                        else:
                            self.assertIsNone(i)

    def test_axis_ancestors(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}...{or_self}'
                    with self.subTest(node=node_type, query=query):
                        expected: typing.List[segments.Types.C_ITO] = []
                        cur = node
                        while (par := cur.parent) is not None:
                            expected.append(par)
                            cur = par
                        if order == '-':
                            expected.reverse()
                        if len(expected) == 0 and or_self == 'S':
                            expected.append(node)
                        actual = [*node.find_all(query)]
                        self.assertListEqual(expected, actual)

    def test_axis_parent(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}..{or_self}'
                    with self.subTest(node=node_type, query=query):
                        i = node.find(query)
                        if node is self.root:
                            if or_self == 'S':
                                self.assertIs(node, i)
                            else:
                                self.assertIsNone(i)
                        else:
                            self.assertIs(node.parent, i)

    def test_axis_self(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                query = f'{order}.'
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
        for order in '', '+', '-':
            query = f'*/../{order}-'
            with self.subTest(query=query):
                rv = [*self.root.find_all(query)]
                self.assertEqual(1, len(rv))
                self.assertIs(self.root, rv[0])
                                                                        
    def test_axis_children(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}*{or_self}'                
                    with self.subTest(node=node_type, query=query):
                        expected = [*node.children]
                        if order == '-':
                            expected.reverse()
                        if len(expected) == 0 and or_self == 'S':
                            expected.append(node)
                        actual = [*node.find_all(query)]
                        self.assertListEqual(expected, actual)

    def test_axis_descendants(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}**{or_self}'                
                    with self.subTest(node=node_type, query=query):
                        expected = [*node.walk_descendants()]
                        if order == '-':
                            expected.reverse()
                        if len(expected) == 0 and or_self == 'S':
                            expected.append(node)
                        actual = [*node.find_all(query)]
                        self.assertListEqual(expected, actual)

    def test_axis_leaves(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}***{or_self}'                
                    with self.subTest(node=node_type, query=query):
                        if node in self.leaves:
                            expected = [node] if or_self == 'S' else []
                        else:
                            step = -1 if order == '-' else 1
                            expected = self.leaves[::step]
                        actual = [*node.find_all(query)]
                        self.assertListEqual(expected, actual)

    def test_prior_siblings(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1]
        }.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}<<{or_self}'                
                    with self.subTest(node=node_type, query=query):
                        expected: typing.List[segments.Types.C_ITO] = []
                        if (p := node.parent) is not None:
                            i = p.children.index(node)
                            expected = p.children[:i]
                            if order != '-':
                                expected.reverse()
                        if len(expected) == 0 and or_self == 'S':
                            expected.append(node)
                        actual = [*node.find_all(query)]
                        self.assertListEqual(expected, actual)

    def test_prior_sibling(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1]
        }.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}<{or_self}'                
                    with self.subTest(node=node_type, query=query):
                        expected: typing.List[segments.Types.C_ITO] = []
                        if (p := node.parent) is not None:
                            i = p.children.index(node)
                            if i > 0:
                                expected = p.children[i - 1:i]
                        if len(expected) == 0 and or_self == 'S':
                            expected.append(node)
                        actual = [*node.find_all(query)]
                        self.assertListEqual(expected, actual)

    def test_next_sibling(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1]
        }.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}>{or_self}'                
                    with self.subTest(node=node_type, query=query):
                        expected: typing.List[segments.Types.C_ITO] = []
                        if (p := node.parent) is not None:
                            i = p.children.index(node)
                            if i < len(p.children) - 1:
                                expected = p.children[i + 1:i + 2]
                        if len(expected) == 0 and or_self == 'S':
                            expected.append(node)
                        actual = [*node.find_all(query)]
                        self.assertListEqual(expected, actual)                        

    def test_next_siblings(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1]
        }.items():
            for order in '', '+', '-':
                for or_self in '', 'S':
                    query = f'{order}>>{or_self}'                
                    with self.subTest(node=node_type, query=query):
                        expected: typing.List[Ito] = []
                        if node.parent is not None:
                            i = node.parent.children.index(node)
                            if i < len(node.parent.children) - 1:
                                expected = node.parent.children[i + 1:]
                                if order == '-':
                                    expected.reverse()
                        if len(expected) == 0 and or_self == 'S':
                            expected.append(node)
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
                    expected = [d for d in node.walk_descendants() if str(d) == s]
                    actual = [*node.find_all(query)]
                    self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_multiple(self):
        for node_type, node in {'root': self.root}.items():
            strings = 'ten', 'eleven', 'twelve'
            query = f'**[s:{",".join(segments.query.escape(s) for s in strings)}]'
            with self.subTest(node=node_type, query=query):
                expected = [d for d in node.walk_descendants() if str(d) in strings]
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
                        expected = [d for d in node.walk_descendants() if str(d).casefold() == s.casefold()]
                        actual = [*node.find_all(query)]
                        self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_casefold_multiple(self):
        for node_type, node in {'root': self.root}.items():
            basis = 'ten', 'ELEVEN', 'twelve'
            for case_func in str.upper, str.casefold, str.lower:
                cfs = [case_func(s) for s in basis]
                query = f'**[scf:{",".join(segments.query.escape(s) for s in cfs)}]'
                with self.subTest(node=node_type, query=query):
                        expected = [d for d in node.walk_descendants() if str(d).casefold() in [s.casefold() for s in cfs]]
                        actual = [*node.find_all(query)]
                        self.assertSequenceEqual(expected, actual)
    
    # endregion

    # region filter index
                
    def test_filter_index_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
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
            for order in '', '+', '-':
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
            for order in '', '+', '-':
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
    
    # region filter predicates
    
    # TODO : Add filter predicates test(s)
    
    # endregion
    
    # region filter values

    def test_filter_values(self):
        values = {'a': 10, 'b': 11, 'c': 13}
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for keys in ('a',), ('a', 'b'), ('b',), ('b', 'c'), ('c',), ('a', 'c'), ('a', 'b', 'c'):
                    query = f'**{order}[v:{",".join(keys)}]'
                    with self.subTest(node=node_type, order=order, keys=keys, query=query):
                        vals = [v for k, v in values.items() if k in keys]
                        tmp = [*node.walk_descendants()]
                        if order == 'r':
                            tmp.reverse()
                        expected = [i for i in tmp if i.value() in vals]
                        actual = [*node.find_all(query, values=values)]
                        self.assertListEqual(expected, actual)

    # endregion

    # endregion

    # region subquery
    
    def test_subquery_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                query = '**' + order + '[d:word]{*[d:char]&[s:e]}'  # words with 'e'
                with self.subTest(node=node_type, order=order, query=query):
                    step = -1 if order == 'r' else 1
                    expected = [*dict.fromkeys(leaf.parent for leaf in self.leaves[::step] if str(leaf) == 'e').keys()]
                    actual = [*node.find_all(query)]
                    self.assertListEqual(expected, actual)
    
    # endregion

    # endregion
