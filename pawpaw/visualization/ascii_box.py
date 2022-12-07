from dataclasses import dataclass
from enum import Enum, auto
import typing

from pawpaw import Errors

# See https://en.wikipedia.org/wiki/Box-drawing_character

@dataclass(frozen=True)
class Style:
    class Weight(Enum):
        LIGHT = auto()
        HEAVY = auto()

    class Count(Enum):
        SINGLE = auto()
        PARALLEL = auto()
        DOUBLE_DASH = auto()
        TRIPLE_DASH = auto()
        QUADRUPLE_DASH = auto()

    weight: Weight = Weight.LIGHT
    count: Count = Count.SINGLE


class Side:
    class Orientation(Enum):
        HORIZONTAL = auto()
        VERTICAL = auto()

    _characters: typing.Dict[str, typing.Tuple[Orientation, Style]] = {
        '─': (Orientation.HORIZONTAL, Style()),
        '━': (Orientation.HORIZONTAL, Style(Style.Weight.HEAVY)),
        '═': (Orientation.HORIZONTAL, Style(count=Style.Count.PARALLEL)),
        '╌': (Orientation.HORIZONTAL, Style(count=Style.Count.DOUBLE_DASH)),
        '╍': (Orientation.HORIZONTAL, Style(Style.Weight.HEAVY, Style.Count.DOUBLE_DASH)),
        '┈': (Orientation.HORIZONTAL, Style(count=Style.Count.TRIPLE_DASH)),
        '┉': (Orientation.HORIZONTAL, Style(Style.Weight.HEAVY, Style.Count.TRIPLE_DASH)),
        '┄': (Orientation.HORIZONTAL, Style(count=Style.Count.QUADRUPLE_DASH)),
        '┅': (Orientation.HORIZONTAL, Style(Style.Weight.HEAVY, Style.Count.QUADRUPLE_DASH)),

        '│': (Orientation.VERTICAL, Style()),
        '┃': (Orientation.VERTICAL, Style(Style.Weight.HEAVY)),
        '║': (Orientation.VERTICAL, Style(count=Style.Count.PARALLEL)),
        '╎': (Orientation.VERTICAL, Style(count=Style.Count.DOUBLE_DASH)),
        '╏': (Orientation.VERTICAL, Style(Style.Weight.HEAVY, Style.Count.DOUBLE_DASH)),
        '┊': (Orientation.VERTICAL, Style(count=Style.Count.TRIPLE_DASH)),
        '┋': (Orientation.VERTICAL, Style(Style.Weight.HEAVY, Style.Count.TRIPLE_DASH)),
        '┆': (Orientation.VERTICAL, Style(count=Style.Count.QUADRUPLE_DASH)),
        '┇': (Orientation.VERTICAL, Style(Style.Weight.HEAVY, Style.Count.QUADRUPLE_DASH)),
    }

    @classmethod
    def _find(cls, orientation: Orientation, style: Style = Style()) -> str:
        for k, v in cls._characters.items():
            if v == (orientation, style):
                return k
        
        raise ValueError(f'no character matches orientation {orientation} and style {style}')

    def __init__(self, style: Style = Style()):
        self._horizontal = self._find(self.Orientation.HORIZONTAL, style)
        self._vertical = self._find(self.Orientation.VERTICAL, style)

    def __getitem__(self, key: Orientation) -> str:
        return getattr(self, key.name)

    @property
    def HORIZONTAL(self) -> str:
        return self._horizontal

    @property
    def VERTICAL(self) -> str:
        return self._vertical


class Corner:
    class Orientation(Enum):
        NW = auto()
        NE = auto()
        SW = auto()
        SE = auto()

    _characters: typing.Dict[str, typing.Tuple[Orientation, Style]] = {
        '┌': (Orientation.NW, Style(), Style()),
        '┎': (Orientation.NW, Style(), Style(Style.Weight.HEAVY)),
        '┍': (Orientation.NW, Style(Style.Weight.HEAVY), Style()),
        '┏': (Orientation.NW, Style(Style.Weight.HEAVY), Style(Style.Weight.HEAVY)),
        '╓': (Orientation.NW, Style(), Style(count=Style.Count.PARALLEL)),
        '╒': (Orientation.NW, Style(count=Style.Count.PARALLEL), Style()),
        '╔': (Orientation.NW, Style(count=Style.Count.PARALLEL), Style(count=Style.Count.PARALLEL)),

        '┐': (Orientation.NE, Style(), Style()),
        '┒': (Orientation.NE, Style(), Style(Style.Weight.HEAVY)),
        '┑': (Orientation.NE, Style(Style.Weight.HEAVY), Style()),
        '┓': (Orientation.NE, Style(Style.Weight.HEAVY), Style(Style.Weight.HEAVY)),
        '╖': (Orientation.NE, Style(), Style(count=Style.Count.PARALLEL)),
        '╕': (Orientation.NE, Style(count=Style.Count.PARALLEL), Style()),
        '╗': (Orientation.NE, Style(count=Style.Count.PARALLEL), Style(count=Style.Count.PARALLEL)),

        '└': (Orientation.SW, Style(), Style()),
        '┖': (Orientation.SW, Style(), Style(Style.Weight.HEAVY)),
        '┕': (Orientation.SW, Style(Style.Weight.HEAVY), Style()),
        '┗': (Orientation.SW, Style(Style.Weight.HEAVY), Style(Style.Weight.HEAVY)),
        '╙': (Orientation.SW, Style(), Style(count=Style.Count.PARALLEL)),
        '╘': (Orientation.SW, Style(count=Style.Count.PARALLEL), Style()),
        '╚': (Orientation.SW, Style(count=Style.Count.PARALLEL), Style(count=Style.Count.PARALLEL)),

        '┘': (Orientation.SE, Style(), Style()),
        '┚': (Orientation.SE, Style(), Style(Style.Weight.HEAVY)),
        '┙': (Orientation.SE, Style(Style.Weight.HEAVY), Style()),
        '┛': (Orientation.SE, Style(Style.Weight.HEAVY), Style(Style.Weight.HEAVY)),
        '╜': (Orientation.SE, Style(), Style(count=Style.Count.PARALLEL)),
        '╛': (Orientation.SE, Style(count=Style.Count.PARALLEL), Style()),
        '╝': (Orientation.SE, Style(count=Style.Count.PARALLEL), Style(count=Style.Count.PARALLEL)),
    }

    @classmethod
    def _find(cls, orientation: Orientation, horizontal_style: Style, vertical_style: Style) -> str:
        for k, v in cls._characters.items():
            if v == (orientation, horizontal_style, vertical_style):
                return k
        
        raise ValueError(f'no character matches orientation {orientation},'
                         f' horizontal_style {horizontal_style},'
                         f' and vertical_style {vertical_style}')

    def __init__(self, horizontal_style: Style = Style(), vertical_style: Style = Style()):
        self._nw = self._find(self.Orientation.NW, horizontal_style, vertical_style)
        self._ne = self._find(self.Orientation.NE, horizontal_style, vertical_style)
        self._sw = self._find(self.Orientation.SW, horizontal_style, vertical_style)
        self._se = self._find(self.Orientation.SE, horizontal_style, vertical_style)

    def __getitem__(self, key: Orientation) -> str:
        return getattr(self, key.name)

    @property
    def NW(self) -> str:
        return self._nw

    @property
    def NE(self) -> str:
        return self._ne

    @property
    def SW(self) -> str:
        return self._sw

    @property
    def SE(self) -> str:
        return self._se


class Box:
    def __init__(self, horizontal_style: Style = Style(), vertical_style: Style = Style()):
        self.hz_side = Side(horizontal_style).HORIZONTAL
        self.vt_side = Side(vertical_style).VERTICAL        
        self.corner = Corner(horizontal_style, vertical_style)

    def from_lines(self, *lines: str) -> typing.List[str]:
        max_line = max(len(line) for line in lines)

        hz = self.hz_side * (max_line + 2)
        rv = [f'{self.corner.NW}{hz}{self.corner.NE}']

        for line in lines:
            rv.append(f'{self.vt_side} {line:^{max_line}} {self.vt_side}')

        rv.append(f'{self.corner.SW}{hz}{self.corner.SE}')

        return rv

    def from_text(self, text: str) -> typing.List[str]:
        return self.from_lines(*text.splitlines())
