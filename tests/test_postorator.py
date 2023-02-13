from itertools import tee

import regex
from pawpaw import Ito, Types
from pawpaw.arborform import Split
from pawpaw.arborform.postorator import Postorator
from tests.util import _TestIto


class TestPostorator(_TestIto):
    post_desc = 'joined'

    @classmethod
    def simple(cls, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        yield Ito.join(*itos)

    def test_traverse(self):
        for s in 'One', 'One Two', 'One Two Three', 'One Two Three Four':
            itos = Ito(s).str_split()
            with self.subTest(string=s, itos=itos, desc=self.post_desc):
                wrapped = Postorator.wrap(self.simple)
                expected = [*self.simple(itos)]
                actual = [*wrapped(itos)]
                self.assertListEqual(expected, actual)

    def test_post(self):
        for s in 'One', 'One Two', 'One Two Three', 'One Two Three Four':
            root = Ito(s, desc='root')
            splitter = Split(regex.compile(r'\s+'))

            rv = [*splitter(root)]
            self.assertListEqual(root.str_split(), rv)

            splitter.postorator = Postorator.wrap(self.simple)
            expected = [Ito(s)]
            actual = [*splitter(root)]
            self.assertListEqual(expected, actual)
