import pawpaw
from tests.util import _TestIto


class TestKeyedList(_TestIto):
    _test_style_data: list[tuple[str, str]]  = [
        (
            'TYPE_1',
"""
-----+-----+-----
  A  |  B  |  C
-----+-----+-----
 aaa | bbb | ccc
-----+-----+-----
"""
        ),
        (
            'TYPE_2',
"""
-------------------
|  A  |  B  |  C  |
|-----------------|
| aaa | bbb | ccc |
-------------------
"""
        )
    ]


    def test_Foo(self) -> None:
        for style_name, data in self._test_style_data:
            with self.subTest(style=style_name):
                style = getattr(pawpaw.table.styles, style_name)
                table = pawpaw.table.StyledTable(style)
                itor = table.get_itor()

                itos = list(itor(pawpaw.Ito(data)))
                self.assertIsNotNone(itos)
                self.assertEqual(1, len(itos))
                ito = itos[0]
                self.assertEqual('table', ito.desc)
                rows = [*ito.find_all('*[d:row]')]
                self.assertEqual(2, len(rows))
