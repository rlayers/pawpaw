import itertools
import typing

import pawpaw
from pawpaw.visualization import sgr


class Highlighter:
    '''
    - Guarrantee differing color across any Ito boundaries
    - An Ito parent might not have the same color for sub spans, because it is not always possible to do so.
      Consider a two-color palete with this nesting:
        A-------------A     Prefix and suffix get color 1
            B------B        Assign color 2 so that boundary AB and BA are visible
            C---C           If color 1, boundary AC is invisible.  If color 2, boundary CB invisible)
    '''

    def __init__(self, palette: sgr.C_PALETTE):
        self._backs = tuple(sgr.Back.from_color(col) for col in palette)

    def _compose(self, predicate: pawpaw.Types.P_ITO, it_back: typing.Iterator[sgr.Back], ito: pawpaw.Ito, str_slice: slice | None = None):
        if predicate(ito):
            prefix = f'{next(it_back)}'
            suffix = f'{sgr.Back.RESET}'
        else:
            prefix = suffix = ''

        if str_slice is None:
            s = f'{ito}'
        else:
            s = f'{ito.string[str_slice]}'

        return f'{prefix}{s}{suffix}'
            
    def _print(self, ito: pawpaw.Types.P_ITO, predicate: pawpaw.Types.P_ITO, it_back: typing.Iterator[sgr.Back]):
        if ito.children == 0:
            if len(ito) == 0:
                print(self._compose(predicate, it_back, ito), end='')
            return

        last = ito.start
        for child in ito.children:
            if last < child.start:
                print(self._compose(predicate, it_back, ito, slice(last, child.start)), end='')
            self._print(child, predicate, it_back)
            last = child.stop
        if last < ito.stop:
            print(self._compose(predicate, it_back, ito, slice(last, ito.stop)), end='')

    def print(self, ito: pawpaw.Ito, predicate: pawpaw.Types.P_ITO = lambda ito: True) -> None:
        self._print(ito, predicate, itertools.cycle(self._backs))
