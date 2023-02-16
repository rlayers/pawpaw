import regex
from pawpaw import Ito
from pawpaw.arborform import Itorator, Filter
from tests.util import _TestIto


class TestFilter(_TestIto):
    def test_traverse_partial(self):
        s = '1a2b3c'
        root = Ito(s)

        split_chr = Itorator.wrap(lambda ito: ito)
        rv = [*split_chr(root)]
        self.assertEqual(len(s), len(rv))

        for ft, f in [('None', lambda ito: False), ('All', lambda ito: True), ('Partial', ito.str_isnumeric)]:
            with self.subTest(filter_type=ft):
                filter = Filter(f)
                split_chr.itor_next = filter
                expected = [i for i in root if f(i)]
                actual = [*split_chr(root)]
                self.assertSequenceEqual(expected, actual)
