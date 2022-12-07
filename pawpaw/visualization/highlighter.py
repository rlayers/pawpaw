import typing

import pawpaw
from pawpaw.visualization import sgr


class Highlighter:
    def __init__(self, *colors: sgr.Color):
        self.palette = tuple(sgr.Back.from_color(col) for col in colors)

    def _rotate_color(self) -> typing.Iterable[sgr.Back]:
        i = 0
        while True:
            yield self.palette[i]
            i += 1
            i %= len(self.palette)
            
    def print(self, ito: pawpaw.Types.C_ITO):
        it_col = self._rotate_color()
        
        stop = 0
        for leaf in ito.find_all('***'):
            if stop < leaf.start:
                print(ito.string[stop:leaf.start], end='')
            print(f'{next(it_col)}{leaf}{sgr.Back.RESET}', end='')
            stop = leaf.stop
        if leaf.stop < len(ito.string):
            print(ito.string[stop:])
