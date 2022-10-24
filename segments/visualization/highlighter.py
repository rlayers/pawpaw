import random
import typing

import regex
import segments
from segments.visualization.sgr import Back, Fore


class Highlighter:
    def __init__(self, *colors: NamedColors):
        self.palette = tuple(Back.from_name(col.name) for col in colors)

    def _rotate_color(self) -> typing.Iterable[Back]:
        i = 0
        while True:
            yield self.palette[i]
            i += 1
            i %= len(self.palette)
            
    def print(self, ito: segments.Types.C_ITO):
        it_col = self._rotate_color()
        
        stop = 0
        for leaf in ito.find_all('***'):
            if stop < leaf.start:
                print(ito.string[stop:leaf.start], end='')
            print(f'{next(it_col)}{leaf}{Back.RESET}', end='')
            stop = leaf.stop
        if leaf.stop < len(ito.string):
            print(ito.string[stop:]
