import itertools
import typing

import regex
from pawpaw import Ito
import pawpaw
from tests.util import _TestIto, IntIto


class TestItoTraversal(_TestIto):
    @classmethod
    def count_descendants(cls, node: pawpaw.Ito) -> int:
        rv = len(node.children)
        for child in node.children:
            rv += cls.count_descendants(child)
        return rv

    def setUp(self) -> None:
        super().setUp()

        self.src = 'nine 9 TEN 10 eleven 11 TWELVE 12 thirteen 13'
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)(?: |$))+')
        m = re.fullmatch(self.src)

        self.root = Ito.from_match(m)
        self.desc = 'root'
        self.descendants_count = self.count_descendants(self.root)

        numbers = [i for i in self.root.walk_descendants() if i.desc == 'number']
        for n in numbers:
            repl = IntIto(n, desc=n.desc)
            repl.children.add(*(IntIto(c, desc=c.desc) for c in n.children))
            p = n.parent
            i = p.children.index(n)
            p.children[i] = repl

        self.leaves = [d for d in self.root.walk_descendants() if len(d.children) == 0]

        self.leaf = next(i for i in self.leaves if str(i.parent) == 'eleven' and str(i) == 'v')

        self.descs = ['root', 'phrase', 'word', 'char']


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


class TestItoQuery(TestItoTraversal):
    #region declarations

    def test_filter_keys_unique(self):
        fks = [*itertools.chain(*pawpaw.query.FILTER_KEYS.values())]
        self.assertSequenceEqual(list(dict.fromkeys(fks)), fks)

    #endregion

    # region axis

    def test_axis_root(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', '!', '!!':
                    path = f'{order}....{or_self}'
                    with self.subTest(node=node_type, path=path):
                        if node is self.root:
                            expected = [self.root] if or_self in ('!', '!!') else []
                        else:
                            expected = [self.root]
                            if or_self == '!!':
                                if order == '-':
                                    expected.append(node)
                                else:
                                    expected.insert(0, node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_axis_ancestors(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', '!', '!!':
                    path = f'{order}...{or_self}'
                    with self.subTest(node=node_type, path=path):
                        expected: typing.List[pawpaw.Ito] = []
                        cur = node
                        while (par := cur.parent) is not None:
                            expected.append(par)
                            cur = par
                        if order == '-':
                            expected.reverse()
                        if len(expected) == 0:
                            if or_self in ('!', '!!'):
                                expected.append(node)
                        elif or_self == '!!':
                            if order == '-':
                                expected.append(node)
                            else:
                                expected.insert(0, node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_axis_parent(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', '!', '!!':
                    path = f'{order}..{or_self}'
                    with self.subTest(node=node_type, path=path):
                        expected: typing.List[pawpaw.Ito] = []
                        if node is self.root:
                            if or_self in ('!', '!!'):
                                expected.append(node)
                        else:
                            expected.append(node.parent)
                            if or_self == '!!':
                                if order == '-':
                                    expected.append(node)
                                else:
                                    expected.insert(0, node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_axis_self(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                path = f'{order}.'
                with self.subTest(node=node_type, path=path):
                    i = node.find(path)
                    self.assertIs(node, i)

    def test_axis_dedup(self):
        non_leaves: list[Ito] = [self.root]
        non_leaves.extend(i for i in self.root.walk_descendants() if len(i.children) != 0)

        # First ensure dups present
        path = f'***/...'
        dups = [*self.root.find_all(path)]
        self.assertLess(len(non_leaves), len(dups))

        # Now make sure they get removed
        for order in '', '+', '-':
            path = f'***/.../{order}><'
            with self.subTest(path=path):
                expected = list({d:None for d in dups}.keys())
                if order == '-':
                    expected.reverse()
                rv = [*self.root.find_all(path)]
                self.assertListEqual(expected, rv)

    def test_axis_children(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}*{or_self}'                
                    with self.subTest(node=node_type, path=path):
                        expected = [*node.children]
                        if order == '-':
                            expected.reverse()
                        if len(expected) == 0 and or_self == '!':
                            expected.append(node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_axis_descendants(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}**{or_self}'                
                    with self.subTest(node=node_type, path=path):
                        expected = [*node.walk_descendants()]
                        if order == '-':
                            expected.reverse()
                        if len(expected) == 0 and or_self == '!':
                            expected.append(node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_axis_leaves(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}***{or_self}'                
                    with self.subTest(node=node_type, path=path):
                        if node in self.leaves:
                            expected = [node] if or_self == '!' else []
                        else:
                            step = -1 if order == '-' else 1
                            expected = self.leaves[::step]
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_preceding(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1],
            'leaf': self.leaf
        }.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}<<<{or_self}'
                    with self.subTest(node=node_type, path=path):
                        if node is self.root:
                            expected: pawpaw.Ito = []
                            if or_self:
                                expected.append(node)
                        else:
                            ancestors: pawpaw.Ito = [node]
                            while (parent := ancestors[-1].parent) is not None:
                                ancestors.append(parent)
                            expected = [*self.root.walk_descendants(order != '-')]
                            i = len(expected)
                            while i > 0:
                                i -= 1
                                cur = expected[i]
                                if node.stop <= cur.start:
                                    del expected[i]
                                elif cur in ancestors:
                                    del expected[i]
                                elif node.start <= cur.start <= cur.stop <= node.stop:  # self & descendants
                                    del expected[i]
                            if len(expected) == 0 and or_self:
                                expected.append(node)

                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)
                        
    def test_prior_siblings(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1]
        }.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}<<{or_self}'                
                    with self.subTest(node=node_type, path=path):
                        expected: typing.List[pawpaw.Ito] = []
                        if (p := node.parent) is not None:
                            i = p.children.index(node)
                            expected = p.children[:i]
                            if order != '-':
                                expected.reverse()
                        if len(expected) == 0 and or_self == '!':
                            expected.append(node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_prior_sibling(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1]
        }.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}<{or_self}'                
                    with self.subTest(node=node_type, path=path):
                        expected: typing.List[pawpaw.Ito] = []
                        if (p := node.parent) is not None:
                            i = p.children.index(node)
                            if i > 0:
                                expected = p.children[i - 1:i]
                        if len(expected) == 0 and or_self == '!':
                            expected.append(node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_next_sibling(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1]
        }.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}>{or_self}'                
                    with self.subTest(node=node_type, path=path):
                        expected: typing.List[pawpaw.Ito] = []
                        if (p := node.parent) is not None:
                            i = p.children.index(node)
                            if i < len(p.children) - 1:
                                expected = p.children[i + 1:i + 2]
                        if len(expected) == 0 and or_self == '!':
                            expected.append(node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)                        

    def test_next_siblings(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1]
        }.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}>>{or_self}'                
                    with self.subTest(node=node_type, path=path):
                        expected: typing.List[Ito] = []
                        if node.parent is not None:
                            i = node.parent.children.index(node)
                            if i < len(node.parent.children) - 1:
                                expected = node.parent.children[i + 1:]
                                if order == '-':
                                    expected.reverse()
                        if len(expected) == 0 and or_self == '!':
                            expected.append(node)
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_following(self):
        for node_type, node in {
            'root': self.root,
            'first-child': self.root.children[0],
            'middle-child': self.root.children[1],
            'last-child': self.root.children[-1],
            'leaf': self.leaf
        }.items():
            for order in '', '+', '-':
                for or_self in '', '!':
                    path = f'{order}>>>{or_self}'
                    with self.subTest(node=node_type, path=path):
                        if node is self.root:
                            expected: pawpaw.Ito = []
                            if or_self:
                                expected.append(node)
                        else:
                            ancestors: pawpaw.Ito = [node]
                            while (parent := ancestors[-1].parent) is not None:
                                ancestors.append(parent)
                            expected = [*self.root.walk_descendants(order == '-')]
                            i = len(expected)
                            while i > 0:
                                i -= 1
                                cur = expected[i]
                                if cur.stop <= node.start:
                                    del expected[i]
                                elif cur in ancestors:
                                    del expected[i]
                                elif cur is node:
                                    del expected[i]
                                elif node.start <= cur.start <= cur.stop <= node.stop:  # self & descendants
                                    del expected[i]
                            if len(expected) == 0 and or_self:
                                expected.append(node)

                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    # endregion

    # region filter
    
    # region filter desc
    
    def test_filter_desc_scalar(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for desc in 'word', 'char':
                for not_option in '', '~':
                    path = f'**[{not_option}d:{desc}]'
                    with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if (d.desc == desc if (not_option == '') else d.desc != desc)]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)
    
    def test_filter_desc_multiple(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            descs = 'word', 'char'
            path = f'**[d:{",".join(descs)}]'
            with self.subTest(node=node_type, path=path):
                expected = [d for d in node.walk_descendants() if d.desc in descs]
                actual = [*node.find_all(path)]
                self.assertSequenceEqual(expected, actual)

    def test_filter_desc_with_emebdded_special_chars(self):
        s = ' The quick brown fox '
        root = Ito(s, 1, -1)
        root.children.add(*root.str_split())
        for i, c in enumerate(root.children):
            c.desc = f'{i}child: [note...]'  # Comma, space, brackets, etc.

        for idxs in [[1], [1, 2]]:
            descs = [pawpaw.query.escape(c.desc) for i, c in enumerate(root.children) if i in idxs]
            desc = ','.join(descs)
            path = f'*[d:{desc}]'
            with self.subTest(path=path):
                expected = [c for i, c in enumerate(root.children) if i in idxs]
                actual = [*root.find_all(path)]
                self.assertListEqual(expected, actual)

    # endregion
    
    # region filter string
    
    def test_filter_string_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for s in 'TEN', 'eleven', 'twelve':
                path = f'**[s:{pawpaw.query.escape(s)}]'
                with self.subTest(node=node_type, path=path):
                    expected = [d for d in node.walk_descendants() if str(d) == s]
                    actual = [*node.find_all(path)]
                    self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_multiple(self):
        for node_type, node in {'root': self.root}.items():
            strings = 'TEN', 'eleven', 'twelve'
            path = f'**[s:{",".join(pawpaw.query.escape(s) for s in strings)}]'
            with self.subTest(node=node_type, path=path):
                expected = [d for d in node.walk_descendants() if str(d) in strings]
                actual = [*node.find_all(path)]
                self.assertSequenceEqual(expected, actual)

    def test_filter_string_with_emebdded_commas(self):
        s = ' The quick brown fox '
        root = Ito(s, 1, -1)
        root.children.add(*root.str_split())

        for idxs in [[1], [1, 2]]:
            substrs = [pawpaw.query.escape(str(c)) for i, c in enumerate(root.children) if i in idxs]
            substr = ','.join(substrs)
            path = f'*[s:{substr}]'
            with self.subTest(path=path):
                expected = [c for i, c in enumerate(root.children) if i in idxs]
                actual = [*root.find_all(path)]
                self.assertListEqual(expected, actual)                
    
    # endregion
    
    # region filter string casefold
    
    def test_filter_string_casefold_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for s in 'ten', 'ELEVEN', 'twelve':
                for case_func in str.upper, str.casefold, str.lower:
                    s = case_func(s)
                    path = f'**[scf:{pawpaw.query.escape(s)}]'
                    with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if str(d).casefold() == s.casefold()]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_casefold_multiple(self):
        for node_type, node in {'root': self.root}.items():
            basis = 'ten', 'ELEVEN', 'twelve'
            for case_func in str.upper, str.casefold, str.lower:
                cfs = [case_func(s) for s in basis]
                path = f'**[scf:{",".join(pawpaw.query.escape(s) for s in cfs)}]'
                with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if str(d).casefold() in [s.casefold() for s in cfs]]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)

    # endregion
       
    # region filter string casefold endswith
                           
    def test_filter_string_casefold_endswith_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for s in 'x', 'n', 'N', 'e':
                for case_func in str.upper, str.casefold, str.lower:
                    s = case_func(s)
                    path = f'**[scfew:{pawpaw.query.escape(s)}]'
                    with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if str(d).casefold().endswith(s.casefold())]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_casefold_endswith_multiple(self):
        for node_type, node in {'root': self.root}.items():
            basis = 'x', 'N', 'e'
            for case_func in str.upper, str.casefold, str.lower:
                cfs = [case_func(s) for s in basis]
                path = f'**[scfew:{",".join(pawpaw.query.escape(s) for s in cfs)}]'
                with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if any(str(d).casefold().endswith(s.casefold()) for s in cfs)]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)  

    # endregion
    
    # region filter string casefold startswith
                           
    def test_filter_string_casefold_startswith_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for s in 'x', 'n', 't':
                for case_func in str.upper, str.casefold, str.lower:
                    s = case_func(s)
                    path = f'**[scfsw:{pawpaw.query.escape(s)}]'
                    with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if str(d).casefold().startswith(s.casefold())]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_casefold_startswith_multiple(self):
        for node_type, node in {'root': self.root}.items():
            basis = 'x', 'n', 't'
            for case_func in str.upper, str.casefold, str.lower:
                cfs = [case_func(s) for s in basis]
                path = f'**[scfsw:{",".join(pawpaw.query.escape(s) for s in cfs)}]'
                with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if any(str(d).casefold().startswith(s.casefold()) for s in cfs)]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)  

    # endregion

    # region filter string endswith
                           
    def test_filter_string_endswith_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for s in 'x', 'n', 'N', 'e':
                for case_func in str.upper, str.casefold, str.lower:
                    s = case_func(s)
                    path = f'**[sew:{pawpaw.query.escape(s)}]'
                    with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if str(d).endswith(s)]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_endswith_multiple(self):
        for node_type, node in {'root': self.root}.items():
            basis = 'x', 'N', 'e'
            for case_func in str.upper, str.casefold, str.lower:
                cfs = [case_func(s) for s in basis]
                path = f'**[sew:{",".join(pawpaw.query.escape(s) for s in cfs)}]'
                with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if any(str(d).endswith(s) for s in cfs)]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)  

    # endregion
    
    # region filter string startswith
                           
    def test_filter_string_startswith_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for s in 'x', 'n', 't':
                for case_func in str.upper, str.casefold, str.lower:
                    s = case_func(s)
                    path = f'**[ssw:{pawpaw.query.escape(s)}]'
                    with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if str(d).startswith(s)]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)
    
    def test_filter_string_startswith_multiple(self):
        for node_type, node in {'root': self.root}.items():
            basis = 'x', 'n', 't'
            for case_func in str.upper, str.casefold, str.lower:
                cfs = [case_func(s) for s in basis]
                path = f'**[ssw:{",".join(pawpaw.query.escape(s) for s in cfs)}]'
                with self.subTest(node=node_type, path=path):
                        expected = [d for d in node.walk_descendants() if any(str(d).startswith(s) for s in cfs)]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)  

    # endregion    
    
    # region filter index
                
    def test_filter_index_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for index in 0, 1, 2:
                    path = f'{order}*[i:{index}]'
                    with self.subTest(node=node_type, order=order, index=index, path=path):
                        expected = [c for c in node.children]
                        if order == '-':
                            expected.reverse()
                        expected = [expected[index]]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)
                
    def test_filter_index_range(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for index in (0, 1), (1, 2), (0, 2):
                    istr = '-'.join(str(i) for i in index)
                    path = f'{order}*[i:{istr}]'
                    with self.subTest(node=node_type, order=order, index=istr, path=path):
                        expected = [c for c in node.children]
                        if order == '-':
                            expected.reverse()
                        expected = expected[slice(*index)]
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)

    def test_filter_index_mix(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for istr, _slices in (('0,2-4,6', (slice(0, 1), slice(2, 4), slice(6, 7))), ):
                    path = f'{order}**[i:{istr}]'
                    with self.subTest(node=node_type, order=order, index=istr, path=path):
                        tmp = [*node.walk_descendants()]
                        if order == '-':
                            tmp.reverse()
                        expected = []
                        for _slice in _slices:
                            expected.extend(tmp[_slice])
                        actual = [*node.find_all(path)]
                        self.assertSequenceEqual(expected, actual)

    # endregion
    
    # region filter predicates

    def test_filter_predicates(self):
        predicates = {'a': lambda ei: ei.ito.desc == 'digit', 'b': lambda ei: ei.ito.desc == 'char'}
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for keys in ('a',), ('a', 'b'), ('b',):
                    path = f'{order}**[p:{",".join(keys)}]'
                    with self.subTest(node=node_type, order=order, keys=keys, path=path):
                        selected = [v for k, v in predicates.items() if k in keys]
                        combined = lambda ei: all(p(ei) for p in selected)
                        expected = [ei.ito for ei in filter(combined, node.walk_descendants_levels(reverse=(order == '-')))]
                        actual = [*node.find_all(path, predicates=predicates)]
                        self.assertListEqual(expected, actual)
    
    # endregion
    
    # region filter values

    def test_filter_values(self):
        values = {'a': 10, 'b': 11, 'c': 13}
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for keys in ('a',), ('a', 'b'), ('b',), ('b', 'c'), ('c',), ('a', 'c'), ('a', 'b', 'c'):
                    path = f'{order}**[v:{",".join(keys)}]'
                    with self.subTest(node=node_type, order=order, keys=keys, path=path):
                        vals = [v for k, v in values.items() if k in keys]
                        tmp = [*node.walk_descendants()]
                        if order == '-':
                            tmp.reverse()
                        expected = [i for i in tmp if i.value() in vals]
                        actual = [*node.find_all(path, values=values)]
                        self.assertListEqual(expected, actual)

    # endregion

    # endregion

    # region subquery
    
    def test_subquery_scalar(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for not_ in '', '~', '~~':
                    path = order + '**' + '[d:word]' + not_ + '{*[d:char]&[s:e]}'  # words with 'e'
                    with self.subTest(node=node_type, order=order, path=path):
                        step = -1 if order == '-' else 1
                        if not_.count('~') % 2 == 0:
                            expected = [d for d in node.walk_descendants() if d.desc == 'word' and any('e' in str(dd) for dd in d.children)]
                        else:
                            expected = [d for d in node.walk_descendants() if d.desc == 'word' and not any('e' in str(dd) for dd in d.children)]
                        if order == '-':
                            expected.reverse()
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_subquery_multiple(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for words in [['nine'], ['nine', 'TEN'], ['twelve', 'TEN']]:
                    subquery = ' | '.join('{.[s:' + w + ']}' for w in words)
                    path = order + '**' + subquery
                    with self.subTest(node=node_type, order=order, path=path):
                        step = -1 if order == '-' else 1
                        expected = [d for d in self.root.walk_descendants() if str(d) in words]
                        expected = expected[::step]
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_subquery_grouped(self):
        for node_type, node in {'root': self.root}.items():
            for order in '', '+', '-':
                for subquery in (
                    '({.[~s:nine]} | {.[s:nine]}) & {*[s:v]}',
                    '(({.[~s:nine]} | {.[s:nine]}) & {*[s:v]})',
                    '{*[s:v]} & ({.[~s:nine]} | {.[s:nine]})',
                    '({*[s:v]} & ({.[~s:nine]} | {.[s:nine]}))',
                ):
                    path = f'{order}**[d:word]{subquery}'
                    with self.subTest(node=node_type, order=order, path=path):
                        step = -1 if order == '-' else 1
                        expected = [d for d in self.root.walk_descendants() if d.desc == 'word' and any(str(c) == 'v' for c in d.children)]
                        expected = expected[::step]
                        actual = [*node.find_all(path)]
                        self.assertListEqual(expected, actual)

    def test_subquery_empty(self):
        for node_type, node in {'root': self.root}.items():
            for path in '.{}', '.({})', '.{.} & {}':
                with self.subTest(node=node_type, path=path):
                    with self.assertRaises(ValueError) as cm:
                        node.find(path)
                    msg = str(cm.exception)
                    self.assertTrue(all(w in msg for w in ['path', 'empty']))

    def test_subquery_identity(self):
        for node_type, node in {'root': self.root}.items():
            for path in '.{.}', '.({.})', '.({.} & {.})':
                with self.subTest(node=node_type, path=path):
                    self.assertEqual(node, node.find(path))

    # endregion

    # region logical operators and combinatorics (EcfFilter)

    def test_ecf_simple_parens(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for count in range(0, 4):
                path = f'.{"(" * count}[d:{node.desc}]{")" * count}'
                with self.subTest(node=node_type, path=path):
                    expected = node
                    actual = node.find(path)
                    self.assertEqual(expected, actual)

        for node_type, node in {'word': next(d for d in self.root.walk_descendants() if d.desc == 'word')}.items():
            for count in range(0, 4):
                path = f'.{"(" * count}' + '{**[d:char]&[s:n]}' + ')' * count
                with self.subTest(node=node_type, path=path):
                    expected = node
                    actual = node.find(path)
                    self.assertEqual(expected, actual)

    def test_ecf_empty_parens(self):
        for node_type, node in {'root': self.root}.items():
            for path in f'.(() & [d:root] & [d:root])', \
                f'.([d:root] & () & [d:root])', \
                f'.([d:root] & [d:root] & ())', \
                '.(() & {.[d:root]} & {.[d:root]})', \
                '.({.[d:root]} & () & {.[d:root]})', \
                '.({.[d:root]} & {.[d:root]} & ())':
                with self.subTest(node=node_type, path=path):
                    with self.assertRaises(ValueError) as cm:
                        node.find(path)
                    msg = str(cm.exception)
                    self.assertTrue(all(w in msg for w in ['empty parentheses']))

    def test_ecf_not_outside_parens(self):
        s = ' The quick brown fox '
        root = Ito(s, 1, -1)
        root.children.add(*root.str_split())

        path_expected_words = {
            '*[s:The] | [s:quick] | [s:brown]': ['The', 'quick', 'brown'],
            '*([s:The] | [s:quick] | [s:brown])': ['The', 'quick', 'brown'],
            '*~([s:The] | [s:quick] | [s:brown])': ['fox'],
            '*[s:The] | ~([s:quick] | [s:brown])': ['The', 'fox'],
        }

        for path, expected in path_expected_words.items():
            with self.subTest(root=root, path=path):
                actual = [str(i) for i in root.find_all(path)]
                self.assertListEqual(expected, actual)

    def test_ecf_unbalanced_parens(self):
        for node_type, node in {'root': self.root, 'leaf': self.leaf}.items():
            for path in f'.([d:{node.desc}] & [d:{node.desc}]', \
                f'.[d:{node.desc}] (& [d:{node.desc}]', \
                f'.[d:{node.desc}] & ([d:{node.desc}]', \
                f'.[d:{node.desc}] & [d:{node.desc}](', \
                f'.)[d:{node.desc}] & [d:{node.desc}]', \
                f'.[d:{node.desc}]) & [d:{node.desc}]', \
                f'.[d:{node.desc}] &) [d:{node.desc}]', \
                f'.[d:{node.desc}] & [d:{node.desc}])', \
                f'.(([d:{node.desc}] & [d:{node.desc}])', \
                f'.([d:{node.desc}] & [d:{node.desc}]))', \
                f'.)[d:{node.desc}] & [d:{node.desc}](':

                with self.subTest(node=node_type, path=path):
                    with self.assertRaises(ValueError) as cm:
                        node.find(path)
                    msg = str(cm.exception)
                    self.assertTrue(all(w in msg for w in ['unbalanced', 'parentheses']))

    def test_ecf_logic_not(self):
        for node_type, node in {'root': self.root, 'middle-child': self.root.children[0], 'leaf': self.leaf}.items():
            for not_option in '', '~', '~~', '~~~':
                path = f'.({not_option}[d:{node.desc}])'
                with self.subTest(node=node_type, path=path):
                    expected = node if len(not_option) % 2 == 0 else None
                    actual = node.find(path)
                    self.assertEqual(expected, actual)

                path = f'.([d:{node.desc}] & {not_option}[d:{node.desc}])'
                with self.subTest(node=node_type, path=path):
                    expected = node if len(not_option) % 2 == 0 else None
                    actual = node.find(path)
                    self.assertEqual(expected, actual)

    def test_ecf_logic_precedence(self):
        s = ' The quick brown fox '
        root = Ito(s, 1, -1)
        root.children.add(*root.str_split())

        path_expected_words = {
            '*[s:The] | ~[s:quick] & [s:brown]': ['The', 'brown'],
            '*([s:The] | ~[s:quick]) & [s:brown]': ['brown'],
            '*[s:The] & ~[s:The] | ~[s:quick]': ['The', 'brown', 'fox'],
            '*[s:The] & (~[s:The] | ~[s:quick])': ['The'],
        }

        for path, expected in path_expected_words.items():
            with self.subTest(root=root, path=path):
                actual = [str(i) for i in root.find_all(path)]
                self.assertListEqual(expected, actual)

    # endregion
