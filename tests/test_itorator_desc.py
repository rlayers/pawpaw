import regex
from pawpaw import Ito
from pawpaw.arborform import Desc
from tests.util import _TestIto


class TestDesc(_TestIto):
    def test_iter(self):
        s = ' abc '
        root = Ito(s, 1, -1)
        self.assertIsNone(root.desc)

        desc = 'changed'
        itor = Desc(desc)
        rv = itor._transform(root)
        self.assertEqual(1, len(rv))

        rv = rv[0]
        self.assertIs(root, rv)
        self.assertEqual(desc, rv.desc)
