import regex
from pawpaw import Ito, arborform
from tests.util import _TestIto


class TestNuco(_TestIto):
    def test_init(self):
        itor_a = arborform.Reflect()
        itor_b = arborform.Desc('123')
        tag = 'abc'
        nuco = arborform.Nuco(itor_a, itor_b, tag=tag)
        self.assertListEqual([itor_a, itor_b], nuco._itorators)
        self.assertEqual(tag, nuco.tag)

    def test_transform(self):
        s = 'She bought 12 eggs'
        root = Ito(s)

        itor_split = arborform.Itorator.wrap(lambda ito: ito.str_split())

        itor_num = arborform.Extract(regex.compile('(?P<number>\d+)'))
        itor_word = arborform.Desc('word')
        
        itor_nuco = arborform.Nuco(itor_num, itor_word)
        con = arborform.Connectors.Delegate(itor_nuco)
        itor_split.connections.append(con)

        root.children.add(*itor_split(root))
        self.assertEqual(len(s.split()), len(root.children))
        for tok in root.children:
            expected = 'number' if tok.str_isdecimal() else 'word'
            self.assertEqual(expected, tok.desc)
