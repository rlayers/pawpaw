import dataclasses
import typing


from pawpaw import PredicatedValue, Furcation, Ito, arborform
from tests.util import _TestIto, IntIto


def len_nonzero(ito: Ito) -> bool:
    return len(ito) > 0

def def_invalid_input_val(i: int) -> bool:
    return i << 1

def def_invalid_ret_val(ito: Ito) -> str:
    return str(ito)


@dataclasses.dataclass
class _TestData:
    name: str
    valid: bool
    value: Furcation.C_ITEM


itor_ltrim_one = arborform.Itorator.wrap(lambda ito: Ito(ito, 1, desc=ito.desc))
itor_rtrim_one = arborform.Itorator.wrap(lambda ito: Ito(ito, stop=-1, desc=ito.desc))
itor_split = arborform.Itorator.wrap(lambda ito: ito.str_split())

class TestFurcation(_TestIto):
    def setUp(self) -> None:
        super().setUp()

        self.test_data = [
            _TestData('PredicatedValue', True, PredicatedValue(len_nonzero, itor_ltrim_one)),
            _TestData('tuple[typing.Callable[[Itorator], bool], R | None]', True, (len_nonzero, itor_ltrim_one)),
            _TestData('typing.Callable[[Itorator], bool]', True, len_nonzero),
            _TestData('Itorator', True, itor_ltrim_one),
            _TestData('None', True, None),
        ]

    def test_append(self):
        monad = Furcation[Ito, arborform.Itorator]()
        for ti in self.test_data:
            with self.subTest(type=ti.name):
                if ti.valid:
                    monad.append(ti.value)
                    self.assertTrue(True)
                else:
                    with self.assertRaises(TypeError):
                        monad.append(ti.value)

    def test_insert(self):
        monad = Furcation[Ito, arborform.Itorator]()
        for ti in self.test_data:
            with self.subTest(type=ti.name):
                if ti.valid:
                    monad.insert(0, ti.value)
                    self.assertTrue(True)
                else:
                    with self.assertRaises(TypeError):
                        monad.insert(0, ti.value)
