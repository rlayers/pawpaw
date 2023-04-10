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
        self.palette = tuple(sgr.Back.from_color(col) for col in palette)

    def _palette_it(self, exclude: sgr.Back | None = None) -> typing.Iterable[sgr.Back]:
        i = 0
        while True:
            rv = self.palette[i]
            if exclude is None or rv is not exclude:
                yield rv
            i += 1
            i %= len(self.palette)
            
    def _compose(self, predicate: pawpaw.Types.P_ITO, palette: typing.Iterable[sgr.Back], ito: pawpaw.Ito, str_slice: slice | None = None):
        if predicate(ito):
            prefix = f'{next(palette)}'
            suffix = f'{sgr.Back.RESET}'
        else:
            prefix = suffix = ''

        if str_slice is None:
            s = f'{ito}'
        else:
            s = f'{ito.string[str_slice]}'

        return f'{prefix}{s}{suffix}'
            
    def _print(self, ito: pawpaw.Types.P_ITO, predicate: pawpaw.Types.P_ITO, palette: typing.Iterable[sgr.Back]):
        if ito.children == 0:
            if len(ito) == 0:
                print(self._compose(predicate, palette, ito), end='')
            return

        last = ito.start
        for child in ito.children:
            if last < child.start:
                print(self._compose(predicate, palette, ito, slice(last, child.start)), end='')
            self._print(child, predicate, palette)
            last = child.stop
        if last < ito.stop:
            print(self._compose(predicate, palette, ito, slice(last, ito.stop)), end='')

    def print(self, ito: pawpaw.Ito, predicate: pawpaw.Types.P_ITO = lambda ito: True) -> None:
        self._print(ito, predicate, self._palette_it())
