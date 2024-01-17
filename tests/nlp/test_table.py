import pawpaw
from tests.util import _TestIto

import regex

class TestKeyedList(_TestIto):
    _test_style_data: list[tuple[str, str]]  = [
#         (
#             'TYPE_1',
# """
# -----+-----+-----
#   A  |  B  |  C
# -----+-----+-----
#  aaa | bbb | ccc
# -----+-----+-----
# """
#         ),
        (
            'TYPE_2',
"""-------------------
|  A  |  B  |  C  |
|-----------------|
| aaa | bbb | ccc |
-------------------"""
        ),
    ]


    def test_Foo(self) -> None:
        for style_name, data in self._test_style_data:
            style: pawpaw.table.StyledTable = getattr(pawpaw.table.styles, style_name)
            table = pawpaw.table.StyledTable(style)
            indents = ['']
            if style.equi_distant_indent:
                indents.extend((' ', '\t', '  ', '\t '))

            for indent in indents:
                with self.subTest(style=style_name, indent=indent):
                    indented_data = '\n'.join([indent + line for line in data.split('\n')])
                    indented_data = pawpaw.Ito(indented_data)

                    if indent == '':
                        self.assertEqual(data, str(indented_data))

                    if style.equi_distant_indent:
                        ed = pawpaw.table.StyledTable._re_equi_ident
                        itor = pawpaw.arborform.Extract(ed)
                        edr = [*itor(indented_data)]
                        self.assertEqual(1, len(edr))
                        self.assertEqual(str(indented_data), str(edr[0]))
                    else:
                        self.assertEqual(data, str(indented_data))

                    itor = table.get_itor()
                    itos = list(itor(indented_data))
                    self.assertIsNotNone(itos)
                    self.assertEqual(1, len(itos))

                    ito = itos[0]
                    self.assertEqual('table', ito.desc)

                    rows = [*ito.find_all('*[d:row]')]
                    self.assertEqual(2, len(rows))
                    self.assertTrue(all(i.desc == 'row' for i in rows))
