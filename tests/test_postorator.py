from itertools import tee

import regex
from pawpaw import Ito, Types
from pawpaw.arborform import Split
from pawpaw.arborform.postorator import Wrap, Split
from tests.util import _TestIto


class TestPostorator(_TestIto):
    post_desc = 'joined'

    @classmethod
    def simple(cls, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        iter_1, iter_2 = tee(itos, 2)
        joined = Ito.join(iter_1, desc=cls.post_desc)
        yield from (Types.C_BITO(False, i) for i in iter_2)
        yield Types.C_BITO(True, joined)

    def test_traverse(self):
        for s in 'One', 'One Two', 'One Two Three', 'One Two Three Four':
            itos = Ito(s).str_split()
            with self.subTest(string=s, itos=itos, desc=self.post_desc):
                wrapped = Wrap(self.simple)
                expected = [Types.C_BITO(False, i) for i in itos]
                expected.append(Types.C_BITO(True, Ito(s, desc=self.post_desc)))
                actual = [*wrapped.traverse(itos)]
                self.assertListEqual(expected, actual)

    def test_post(self):
        for s in 'One', 'One Two', 'One Two Three', 'One Two Three Four':
            root = Ito(s, desc='root')
            splitter = Split(regex.compile(r'\s+'))

            rv = [*splitter.traverse(root)]
            self.assertListEqual(root.str_split(), rv)

            splitter.postorator = Wrap(self.simple)
            expected = [Ito(s, desc=self.post_desc)]
            actual = [*splitter.traverse(root)]
            self.assertListEqual(expected, actual)
