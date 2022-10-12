import typing
from unittest import TestCase


import regex
from segments import Ito
from segments.tests.util import _TestIto


class TestItoQuery(_TestIto):
    def setUp(self) -> None:
        super().setUp

        self.src = 'nine 9 ten 10 eleven 11 twelve 12 thirteen 13'
        re = regex.compile(r'(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+)(?: |$))+')
        
        self.root = Ito(self.src, self.src.index('ten'), self.src.index('thirteen') - 1, desc='root')
        self.root.children.add(*Ito.from_re(re, self.root))
        self.leaves = [d for d in self.root.walk_descendants() if len(d.children) == 0]
        self.leaf = next(i for i in self.leaves if i.parent[:] == 'eleven' and i[:] == 'v')
                                                                        
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

