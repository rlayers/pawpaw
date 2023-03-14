import regex
from pawpaw import Ito
from pawpaw.arborform import Itorator, Filter, Connectors
from tests.util import _TestIto


class TestFilter(_TestIto):
    def test_traverse_partial(self):
        s = '1a2b3c'
        root = Ito(s)

        split_chr = Itorator.wrap(lambda ito: ito)
        rv = [*split_chr(root)]
        self.assertEqual(len(s), len(rv))

        for ft, f in [('None', lambda ito: False), ('All', lambda ito: True), ('Partial', Ito.str_isnumeric)]:
            with self.subTest(filter_type=ft):
                split_chr = split_chr.clone()
                filter = Filter(f)
                con = Connectors.Delegate(filter)
                split_chr.connections.append(con)
                expected = [i for i in root if f(i)]
                actual = [*split_chr(root)]
                self.assertSequenceEqual(expected, actual)
