from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum, auto, unique
import itertools
import typing

from pawpaw import Errors, Ito, Types, nuco

# See 
# 1. https://en.wikipedia.org/wiki/Box-drawing_character
# 2. https://www.unicode.org/charts/PDF/U2500.pdf

@unique
class Direction(IntEnum):
    N  = 0 * 45
    NE = 1 * 45
    E  = 2 * 45
    SE = 3 * 45
    S  = 4 * 45
    SW = 5 * 45
    W  = 6 * 45
    NW = 7 * 45

    @classmethod
    def from_degrees(cls, degrees: int) -> Direction:
        degrees %= 360
        it = iter(cls)
        for r in range(0, degrees // 45 + 1):
            rv = next(it)
        return rv

    def rotate(self, degrees: int) -> Direction:
        return self.from_degrees(self.value + degrees)

    def reflect(self, surface: Direction) -> Direction:
        delta = surface.value - self.value
        return self.rotate(delta * 2)


@dataclass(frozen=True)    
class Style:
    class Weight(Enum):
        LIGHT = auto()
        HEAVY = auto()

    class Count(Enum):
        SINGLE = auto()
        DOUBLE = auto()

    class Dash(Enum):
        NONE = auto()
        DOUBLE = auto()
        TRIPLE = auto()
        QUADRUPLE = auto()

    class Path(Enum):
        LINE_SEGMENT = auto()
        ARC = auto()

    weight: Weight = Weight.LIGHT
    count: Count = Count.SINGLE
    dash: Dash = Dash.NONE
    path: Path = Path.LINE_SEGMENT


@dataclass
class DirectionStyle:
    direction: Direction
    style: Style

    def rotate(self, degrees: int) -> DirectionStyle:
        return DirectionStyle(self.direction.rotate(degrees), self.style)

    def reflect(self, surface: Direction) -> DirectionStyle:
        return DirectionStyle(self.direction.reflect(surface), self.style)


class BoxDrawingChar:
    _instances: typing.List[BoxDrawingChar] = []

    @classmethod
    def _sort(cls, *direction_styles: DirectionStyle) -> typing.Tuple[DirectionStyle]:
        return tuple(sorted(direction_styles, key=lambda ds: ds.direction.value))

    @classmethod
    def from_char(cls, char: str) -> BoxDrawingChar:
        if (rv := next(filter(lambda bdc: bdc._char == char, cls._instances), None)) is None:
            raise ValueError('parameter \'char\' is not a box-drawing character')
        return rv

    @classmethod
    def from_name(cls, name: str) -> BoxDrawingChar:
        if (rv := next(filter(lambda bdc: bdc._name == name, cls._instances), None)) is None:
            raise ValueError('no box-drawing character matches {name}')
        return rv

    @classmethod
    def _distance(cls, candidate: BoxDrawingChar, *target_direction_styles: DirectionStyle) -> int:
        rv = 0
        for ds_target in target_direction_styles:
            if (ds_candidate := next((ds for ds in candidate.direction_styles if ds.direction == ds_target.direction), None)) is None:
                rv += 4
            else:
                if ds_target.style.weight != ds_candidate.style.weight:
                    rv += 1
                if ds_target.style.count != ds_candidate.style.count:
                    rv += 1
                if ds_target.style.dash != ds_candidate.style.dash:
                    rv += 1
                if ds_target.style.path != ds_candidate.style.path:
                    rv += 1
        
        return rv

    @classmethod
    def from_direction_styles(cls, *direction_styles: DirectionStyle, fuzzy: bool = False) -> BoxDrawingChar:
        best_score: int = -1
        best_bdc: BoxDrawingChar
        for instance in filter(lambda i: len(i.direction_styles) == len(direction_styles), cls._instances):
            d = cls._distance(instance, *direction_styles)
            if fuzzy:
                if best_score == -1 or d < best_score:
                    best_score, best_bdc = d, instance
            else:
                if d == 0:
                    return instance

        if fuzzy:
            return best_bdc
        else:
            raise ValueError(f'no box-drawing character matches {direction_styles}')

    def __init__(self, char: str, name: str, *direction_styles: DirectionStyle):
        self._char: str = char
        self._name: str = name
        self._direction_styles: typing.Tuple[DirectionStyle] = self._sort(*direction_styles)

    @property
    def char(self) -> str:
        return self._char

    @property
    def name(self) -> str:
        return self._name

    @property
    def direction_styles(self) -> typing.Tuple[DirectionStyle]:
        return self._direction_styles

    def __str__(self):
        return self._char

    def rotate(self, degrees: int) -> BoxDrawingChar:
        dss = [ds.rotate(degrees) for ds in self._direction_styles]
        return self.from_direction_styles(*dss, fuzzy=True)

    def reflect(self, surface: Direction) -> BoxDrawingChar:
        dss = [ds.reflect(surface) for ds in self._direction_styles]
        return self.from_direction_styles(*dss, fuzzy=True)


#region Populate Box Drawing Character Instances

BoxDrawingChar._instances.extend(
    (
        #region Light and heavy solid lines

        BoxDrawingChar(
            '─',
            'BOX DRAWINGS LIGHT HORIZONTAL',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '━',
            'BOX DRAWINGS HEAVY HORIZONTAL',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '│',
            'BOX DRAWINGS LIGHT VERTICAL',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┃',
            'BOX DRAWINGS HEAVY VERTICAL',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),

        #endregion

        #region Light and heavy dashed lines

        BoxDrawingChar(
            '┄',
            'BOX DRAWINGS LIGHT TRIPLE DASH HORIZONTAL',
            DirectionStyle(Direction.W, Style(dash=Style.Dash.TRIPLE)),
            DirectionStyle(Direction.E, Style(dash=Style.Dash.TRIPLE)),
        ),
        BoxDrawingChar(
            '┅',
            'BOX DRAWINGS HEAVY TRIPLE DASH HORIZONTAL',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.TRIPLE)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.TRIPLE)),
        ),
        BoxDrawingChar(
            '┆',
            'BOX DRAWINGS LIGHT TRIPLE DASH VERTICAL',
            DirectionStyle(Direction.N, Style(dash=Style.Dash.TRIPLE)),
            DirectionStyle(Direction.S, Style(dash=Style.Dash.TRIPLE)),
        ),
        BoxDrawingChar(
            '┇',
            'BOX DRAWINGS HEAVY TRIPLE DASH VERTICAL',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.TRIPLE)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.TRIPLE)),
        ),
        BoxDrawingChar(
            '┈',
            'BOX DRAWINGS LIGHT QUADRUPLE DASH HORIZONTAL',
            DirectionStyle(Direction.W, Style(dash=Style.Dash.QUADRUPLE)),
            DirectionStyle(Direction.E, Style(dash=Style.Dash.QUADRUPLE)),
        ),
        BoxDrawingChar(
            '┉',
            'BOX DRAWINGS HEAVY QUADRUPLE DASH HORIZONTAL',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.QUADRUPLE)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.QUADRUPLE)),
        ),
        BoxDrawingChar(
            '┊',
            'BOX DRAWINGS LIGHT QUADRUPLE DASH VERTICAL',
            DirectionStyle(Direction.N, Style(dash=Style.Dash.QUADRUPLE)),
            DirectionStyle(Direction.S, Style(dash=Style.Dash.QUADRUPLE)),
        ),
        BoxDrawingChar(
            '┋',
            'BOX DRAWINGS HEAVY QUADRUPLE DASH VERTICAL',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.QUADRUPLE)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.QUADRUPLE)),
        ),

        #endregion

        #region Light and heavy line box components

        BoxDrawingChar(
            '┌',
            'BOX DRAWINGS LIGHT DOWN AND RIGHT',
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┍',
            'BOX DRAWINGS DOWN LIGHT AND RIGHT HEAVY',
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┎',
            'BOX DRAWINGS DOWN HEAVY AND RIGHT LIGHT',
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┏',
            'BOX DRAWINGS HEAVY DOWN AND RIGHT',
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┐',
            'BOX DRAWINGS LIGHT DOWN AND LEFT',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┑',
            'BOX DRAWINGS DOWN LIGHT AND LEFT HEAVY',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┒',
            'BOX DRAWINGS DOWN HEAVY AND LEFT LIGHT',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┓',
            'BOX DRAWINGS HEAVY DOWN AND LEFT',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '└',
            'BOX DRAWINGS LIGHT UP AND RIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '┕',
            'BOX DRAWINGS UP LIGHT AND RIGHT HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┖',
            'BOX DRAWINGS UP HEAVY AND RIGHT LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '┗',
            'BOX DRAWINGS HEAVY UP AND RIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┘',
            'BOX DRAWINGS LIGHT UP AND LEFT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
        ),
        BoxDrawingChar(
            '┙',
            'BOX DRAWINGS UP LIGHT AND LEFT HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┚',
            'BOX DRAWINGS UP HEAVY AND LEFT LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
        ),
        BoxDrawingChar(
            '┛',
            'BOX DRAWINGS HEAVY UP AND LEFT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '├',
            'BOX DRAWINGS LIGHT VERTICAL AND RIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┝',
            'BOX DRAWINGS VERTICAL LIGHT AND RIGHT HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┞',
            'BOX DRAWINGS UP HEAVY AND RIGHT DOWN LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┟',
            'BOX DRAWINGS DOWN HEAVY AND RIGHT UP LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┠',
            'BOX DRAWINGS VERTICAL HEAVY AND RIGHT LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┡',
            'BOX DRAWINGS DOWN LIGHT AND RIGHT UP HEAVY',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┢',
            'BOX DRAWINGS UP LIGHT AND RIGHT DOWN HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┣',
            'BOX DRAWINGS HEAVY VERTICAL AND RIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┤',
            'BOX DRAWINGS LIGHT VERTICAL AND LEFT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┥',
            'BOX DRAWINGS VERTICAL LIGHT AND LEFT HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┦',
            'BOX DRAWINGS UP HEAVY AND LEFT DOWN LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┧',
            'BOX DRAWINGS DOWN HEAVY AND LEFT UP LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┨',
            'BOX DRAWINGS VERTICAL HEAVY AND LEFT LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┩',
            'BOX DRAWINGS DOWN LIGHT AND LEFT UP HEAVY',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┪',
            'BOX DRAWINGS UP LIGHT AND LEFT DOWN HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┫',
            'BOX DRAWINGS HEAVY VERTICAL AND LEFT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┬',
            'BOX DRAWINGS LIGHT DOWN AND HORIZONTAL',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┭',
            'BOX DRAWINGS LEFT HEAVY AND RIGHT DOWN LIGHT',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┮',
            'BOX DRAWINGS RIGHT HEAVY AND LEFT DOWN LIGHT',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┯',
            'BOX DRAWINGS DOWN LIGHT AND HORIZONTAL HEAVY',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┰',
            'BOX DRAWINGS DOWN HEAVY AND HORIZONTAL LIGHT',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┱',
            'BOX DRAWINGS RIGHT LIGHT AND LEFT DOWN HEAVY',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┲',
            'BOX DRAWINGS LEFT LIGHT AND RIGHT DOWN HEAVY',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┳',
            'BOX DRAWINGS HEAVY DOWN AND HORIZONTAL',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┴',
            'BOX DRAWINGS LIGHT UP AND HORIZONTAL',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '┵',
            'BOX DRAWINGS LEFT HEAVY AND RIGHT UP LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '┶',
            'BOX DRAWINGS RIGHT HEAVY AND LEFT UP LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┷',
            'BOX DRAWINGS UP LIGHT AND HORIZONTAL HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┸',
            'BOX DRAWINGS UP HEAVY AND HORIZONTAL LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '┹',
            'BOX DRAWINGS RIGHT LIGHT AND LEFT UP HEAVY',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '┺',
            'BOX DRAWINGS LEFT LIGHT AND RIGHT UP HEAVY',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┻',
            'BOX DRAWINGS HEAVY UP AND HORIZONTAL',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '┼',
            'BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┽',
            'BOX DRAWINGS LEFT HEAVY AND RIGHT VERTICAL LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┾',
            'BOX DRAWINGS RIGHT HEAVY AND LEFT VERTICAL LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '┿',
            'BOX DRAWINGS VERTICAL LIGHT AND HORIZONTAL HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╀',
            'BOX DRAWINGS UP HEAVY AND DOWN HORIZONTAL LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╁',
            'BOX DRAWINGS DOWN HEAVY AND UP HORIZONTAL LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╂',
            'BOX DRAWINGS VERTICAL HEAVY AND HORIZONTAL LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╃',
            'BOX DRAWINGS LEFT UP HEAVY AND RIGHT DOWN LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╄',
            'BOX DRAWINGS RIGHT UP HEAVY AND LEFT DOWN LIGHT',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╅',
            'BOX DRAWINGS LEFT DOWN HEAVY AND RIGHT UP LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╆',
            'BOX DRAWINGS RIGHT DOWN HEAVY AND LEFT UP LIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╇',
            'BOX DRAWINGS DOWN LIGHT AND UP HORIZONTAL HEAVY',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╈',
            'BOX DRAWINGS UP LIGHT AND DOWN HORIZONTAL HEAVY',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╉',
            'BOX DRAWINGS RIGHT LIGHT AND LEFT VERTICAL HEAVY',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╊',
            'BOX DRAWINGS LEFT LIGHT AND RIGHT VERTICAL HEAVY',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╋',
            'BOX DRAWINGS HEAVY VERTICAL AND HORIZONTAL',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),

        #endregion

        #region Light and heavy dashed lines

        BoxDrawingChar(
            '╌',
            'BOX DRAWINGS LIGHT DOUBLE DASH HORIZONTAL',
            DirectionStyle(Direction.W, Style(dash=Style.Dash.DOUBLE)),
            DirectionStyle(Direction.E, Style(dash=Style.Dash.DOUBLE)),
        ),
        BoxDrawingChar(
            '╍',
            'BOX DRAWINGS HEAVY DOUBLE DASH HORIZONTAL',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.DOUBLE)),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.DOUBLE)),
        ),
        BoxDrawingChar(
            '╎',
            'BOX DRAWINGS LIGHT DOUBLE DASH VERTICAL',
            DirectionStyle(Direction.N, Style(dash=Style.Dash.DOUBLE)),
            DirectionStyle(Direction.S, Style(dash=Style.Dash.DOUBLE)),
        ),
        BoxDrawingChar(
            '╏',
            'BOX DRAWINGS HEAVY DOUBLE DASH VERTICAL',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.DOUBLE)),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY, dash=Style.Dash.DOUBLE)),
        ),

        #endregion

        #region Light and double line box components

        BoxDrawingChar(
            '═',
            'BOX DRAWINGS DOUBLE HORIZONTAL',
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '║',
            'BOX DRAWINGS DOUBLE VERTICAL',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╒',
            'BOX DRAWINGS DOWN SINGLE AND RIGHT DOUBLE',
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╓',
            'BOX DRAWINGS DOWN DOUBLE AND RIGHT SINGLE',
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╔',
            'BOX DRAWINGS DOUBLE DOWN AND RIGHT',
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╕',
            'BOX DRAWINGS DOWN SINGLE AND LEFT DOUBLE',
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╖',
            'BOX DRAWINGS DOWN DOUBLE AND LEFT SINGLE',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╗',
            'BOX DRAWINGS DOUBLE DOWN AND LEFT',
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╘',
            'BOX DRAWINGS UP SINGLE AND RIGHT DOUBLE',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╙',
            'BOX DRAWINGS UP DOUBLE AND RIGHT SINGLE',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '╚',
            'BOX DRAWINGS DOUBLE UP AND RIGHT',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╛',
            'BOX DRAWINGS UP SINGLE AND LEFT DOUBLE',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╜',
            'BOX DRAWINGS UP DOUBLE AND LEFT SINGLE',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.W, Style()),
        ),
        BoxDrawingChar(
            '╝',
            'BOX DRAWINGS DOUBLE UP AND LEFT',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╞',
            'BOX DRAWINGS VERTICAL SINGLE AND RIGHT DOUBLE',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╟',
            'BOX DRAWINGS VERTICAL DOUBLE AND RIGHT SINGLE',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╠',
            'BOX DRAWINGS DOUBLE VERTICAL AND RIGHT',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╡',
            'BOX DRAWINGS VERTICAL SINGLE AND LEFT DOUBLE',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╢',
            'BOX DRAWINGS VERTICAL DOUBLE AND LEFT SINGLE',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╣',
            'BOX DRAWINGS DOUBLE VERTICAL AND LEFT',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╤',
            'BOX DRAWINGS DOWN SINGLE AND HORIZONTAL DOUBLE',
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╥',
            'BOX DRAWINGS DOWN DOUBLE AND HORIZONTAL SINGLE',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╦',
            'BOX DRAWINGS DOUBLE DOWN AND HORIZONTAL',
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╧',
            'BOX DRAWINGS UP SINGLE AND HORIZONTAL DOUBLE',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╨',
            'BOX DRAWINGS UP DOUBLE AND HORIZONTAL SINGLE',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '╩',
            'BOX DRAWINGS DOUBLE UP AND HORIZONTAL',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╪',
            'BOX DRAWINGS VERTICAL SINGLE AND HORIZONTAL DOUBLE',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╫',
            'BOX DRAWINGS VERTICAL DOUBLE AND HORIZONTAL SINGLE',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),
        BoxDrawingChar(
            '╬',
            'BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL',
            DirectionStyle(Direction.N, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.W, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.E, Style(count=Style.Count.DOUBLE)),
            DirectionStyle(Direction.S, Style(count=Style.Count.DOUBLE)),
        ),

        #endregion

        #region Character cell arcs

        BoxDrawingChar(
            '╭',
            'BOX DRAWINGS LIGHT ARC DOWN AND RIGHT',
            DirectionStyle(Direction.E, Style(path=Style.Path.ARC)),
            DirectionStyle(Direction.S, Style(path=Style.Path.ARC)),
        ),
        BoxDrawingChar(
            '╮',
            'BOX DRAWINGS LIGHT ARC DOWN AND LEFT',
            DirectionStyle(Direction.W, Style(path=Style.Path.ARC)),
            DirectionStyle(Direction.S, Style(path=Style.Path.ARC)),
        ),
        BoxDrawingChar(
            '╯',
            'BOX DRAWINGS LIGHT ARC UP AND LEFT',
            DirectionStyle(Direction.N, Style(path=Style.Path.ARC)),
            DirectionStyle(Direction.W, Style(path=Style.Path.ARC)),
        ),
        BoxDrawingChar(
            '╰',
            'BOX DRAWINGS LIGHT ARC UP AND RIGHT',
            DirectionStyle(Direction.N, Style(path=Style.Path.ARC)),
            DirectionStyle(Direction.E, Style(path=Style.Path.ARC)),
        ),

        #endregion

        #region Character cell diagonals

        BoxDrawingChar(
            '╱',
            'BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT',
            DirectionStyle(Direction.NE, Style()),
            DirectionStyle(Direction.SW, Style()),
        ),
        BoxDrawingChar(
            '╲',
            'BOX DRAWINGS LIGHT DIAGONAL UPPER LEFT TO LOWER RIGHT',
            DirectionStyle(Direction.NW, Style()),
            DirectionStyle(Direction.SE, Style()),
        ),
        BoxDrawingChar(
            '╳',
            'BOX DRAWINGS LIGHT DIAGONAL CROSS',
            DirectionStyle(Direction.NW, Style()),
            DirectionStyle(Direction.NE, Style()),
            DirectionStyle(Direction.SW, Style()),
            DirectionStyle(Direction.SE, Style()),
        ),

        #endregion

        #region Light and heavy half lines

        BoxDrawingChar(
            '╴',
            'BOX DRAWINGS LIGHT LEFT',
            DirectionStyle(Direction.W, Style()),
        ),
        BoxDrawingChar(
            '╵',
            'BOX DRAWINGS LIGHT UP',
            DirectionStyle(Direction.N, Style()),
        ),
        BoxDrawingChar(
            '╶',
            'BOX DRAWINGS LIGHT RIGHT',
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '╷',
            'BOX DRAWINGS LIGHT DOWN',
            DirectionStyle(Direction.S, Style()),
        ),
        BoxDrawingChar(
            '╸',
            'BOX DRAWINGS HEAVY LEFT',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╹',
            'BOX DRAWINGS HEAVY UP',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╺',
            'BOX DRAWINGS HEAVY RIGHT',
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╻',
            'BOX DRAWINGS HEAVY DOWN',
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),

        #endregion

        #region Mixed light and heavy lines

        BoxDrawingChar(
            '╼',
            'BOX DRAWINGS LIGHT LEFT AND HEAVY RIGHT',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╽',
            'BOX DRAWINGS LIGHT UP AND HEAVY DOWN',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.S, Style(weight=Style.Weight.HEAVY)),
        ),
        BoxDrawingChar(
            '╾',
            'BOX DRAWINGS HEAVY LEFT AND LIGHT RIGHT',
            DirectionStyle(Direction.W, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.E, Style()),
        ),
        BoxDrawingChar(
            '╿',
            'BOX DRAWINGS HEAVY UP AND LIGHT DOWN',
            DirectionStyle(Direction.N, Style(weight=Style.Weight.HEAVY)),
            DirectionStyle(Direction.S, Style()),
        ),

        #endregion
    )
)

#endregion


class Boxer:
    def __init__(
        self,
        nw: BoxDrawingChar | str,
        n: BoxDrawingChar | str,
        ne: BoxDrawingChar | str,
        w: BoxDrawingChar | str,
        e: BoxDrawingChar | str,
        sw: BoxDrawingChar | str,
        s: BoxDrawingChar | str,
        se: BoxDrawingChar | str
    ):
        if not (isinstance(nw, BoxDrawingChar) or isinstance(nw, str)):
            raise Errors.parameter_invalid_type('nw', nw, BoxDrawingChar, str)
        self.nw = nw

        if not (isinstance(n, BoxDrawingChar) or isinstance(n, str)):
            raise Errors.parameter_invalid_type('n', n, BoxDrawingChar, str)
        self.n = n

        if not (isinstance(ne, BoxDrawingChar) or isinstance(ne, str)):
            raise Errors.parameter_invalid_type('ne', ne, BoxDrawingChar, str)
        self.ne = ne

        if not (isinstance(w, BoxDrawingChar) or isinstance(w, str)):
            raise Errors.parameter_invalid_type('w', w, BoxDrawingChar, str)
        self.w = w

        if not (isinstance(e, BoxDrawingChar) or isinstance(e, str)):
            raise Errors.parameter_invalid_type('e', e, BoxDrawingChar, str)
        self.e = e

        if not (isinstance(sw, BoxDrawingChar) or isinstance(sw, str)):
            raise Errors.parameter_invalid_type('sw', sw, BoxDrawingChar, str)
        self.sw = sw

        if not (isinstance(s, BoxDrawingChar) or isinstance(s, str)):
            raise Errors.parameter_invalid_type('s', s, BoxDrawingChar, str)
        self.s = s

        if not (isinstance(se, BoxDrawingChar) or isinstance(se, str)):
            raise Errors.parameter_invalid_type('se', se, BoxDrawingChar, str)
        self.se = se

    def _from_lines(self, *lines: Ito) -> typing.List[str]:
        # TODO: Handle SGR, unicode modifying graphemes, etc. to
        # get max column width of printed lines
        max_line = max(sum(1 for c in line if c.isprintable()) for line in lines)

        rv = [f'{self.nw}{str(self.n) * (max_line + 2)}{self.ne}']

        for line in lines:
            rv.append(f'{self.w} {str(line):^{max_line}} {self.e}')

        rv.append(f'{self.sw}{str(self.s) * (max_line + 2)}{self.se}')

        return rv

    def from_srcs(self, *srcs: Ito | str) -> typing.List[str]:
        lines: typing.List[Ito] = []
        for src in srcs:
            if isinstance(src, str):
                src = Ito(src)
            elif not isinstance(src, Ito):
                raise Errors.parameter_invalid_type('srcs', src, Ito, str)
            lines.extend(src.str_splitlines())

        return self._from_lines(*lines)


def _get_direction_styles(bdc: BoxDrawingChar, *directions: Direction) -> typing.Tuple[DirectionStyle | None]:
    return tuple(
        next(filter(lambda ds: ds.direction == d, bdc.direction_styles), None)
        for d
        in directions
    )


def _prior_idx(i: int, count: int) -> int:
    return (i + count - 1) % count


def _next_idx(i: int, count: int) -> int:
    return (i + 1) % count


def from_sides(
    n: str | BoxDrawingChar | None = None,
    w: str | BoxDrawingChar | None = None,
    e: str | BoxDrawingChar | None = None,
    s: str | BoxDrawingChar | None = None
    ) -> Boxer:
    sides = [[Direction.N, n], [Direction.E, e], [Direction.S, s], [Direction.W, w]]

    first_index = next(i for i in range(4) if sides[i][1] is not None)
    if first_index is None:
        raise ValueError('at least one side is required')

    for d, v in sides:
        if isinstance(v, str):
            side = BoxDrawingChar.from_char(v)
        elif not (isinstance(v, BoxDrawingChar) or v is None):
            raise Errors.parameter_invalid_type(d.name.lower(), v, str, BoxDrawingChar, None)

    if sum(1 for s in sides if s[1] is None) == 3:
        for i in range(3):
            prior_idx = (first_index + i) % 4
            cur_idx = (prior_idx + 1) % 4
            # sides[cur_idx][1] = sides[prior_idx][1].rotate(90)
            sides[cur_idx][1] = sides[prior_idx][1].reflect(sides[prior_idx][0].rotate(45))

    else:
        for name, bdc in filter(lambda dv: dv[0] in (Direction.N, Direction.S) and dv[1] is not None, sides):
            if any(ds is None for ds in _get_direction_styles(bdc, Direction.W, Direction.E)):
                raise ValueError(f'parameter {name} lacks Direction.W and Direction.E')

        for name, bdc in filter(lambda dv: dv[0] in (Direction.W, Direction.E) and dv[1] is not None, sides):
            if any(ds is None for ds in _get_direction_styles(bdc, Direction.N, Direction.S)):
                raise ValueError(f'parameter {name} lacks Direction.N and Direction.S')

        for i in range(0, 3):
            prior_idx = (first_index + i) % 4
            cur_idx = (prior_idx + 1) % 4
            next_idx = (cur_idx + 1) % 4

            if sides[cur_idx][1] is not None:
                continue

            if sides[next_idx][1] is None:
                sides[cur_idx][1] = sides[prior_idx][1].rotate(90)
                continue

            d = sides[cur_idx][0]
            prior = sides[prior_idx][1]
            next_ = sides[next_idx][1]

            ds1 = _get_direction_styles(prior, d)[0].rotate(-90)
            ds2 = _get_direction_styles(next_, d)[0].rotate(90)

            sides[cur_idx][1] = BoxDrawingChar.from_direction_styles(ds1, ds2, fuzzy=True)

    corners: typing.List[BoxDrawingChar] = []
    for i in range(0, 4):
        direction = Direction.W.rotate(i * 90)
        s1 = _get_direction_styles(sides[i][1], direction)[0]

        direction = direction.rotate(-90)
        i2 = (i + 1) % 4
        s2 = _get_direction_styles(sides[i2][1], direction)[0]

        corners.append(BoxDrawingChar.from_direction_styles(s1, s2, fuzzy=True))

    return Boxer(
        corners[3], sides[0][1], corners[0],
        sides[3][1], sides[1][1],
        corners[2], sides[2][1], corners[1]
    )


def from_corners(*corners: str | BoxDrawingChar) -> Boxer:
    if len(corners) == 0:
        raise ValueError('at least one corner is required')
    elif len(corners) > 4:
        raise ValueError('more than four corners were supplied')

    tmp: typing.List[typing.List[typing.Tuple[Direction, Direction], BoxDrawingChar | None]] = [
        [(Direction.E, Direction.S), None],
        [(Direction.S, Direction.W), None],
        [(Direction.W, Direction.N), None],
        [(Direction.N, Direction.E), None]
    ]

    corners = [c if isinstance(c, BoxDrawingChar) else BoxDrawingChar.from_char(c) for c in corners]

    scores: typing.List[typing.Dict[int, int]] = [{} for i in range(4)]
    for i, directions in enumerate(t[0] for t in tmp):
        for j, corner in enumerate(corners):
            scores[i][j] = sum(1 for ds in _get_direction_styles(corner, *directions) if ds is not None)

    best_permutation, best_score  = None, None
    best_possible = len(corners) * 2
    for p in itertools.permutations([0, 1, 2, 3], len(corners)):
        score = sum(2 if (score := scores[j][i]) >= 2 else score for i, j in enumerate(p))
        if score == best_possible:
            best_permutation = p
            best_score = score
            break
        elif best_permutation is None or score > best_score:
            best_permutation = p
            best_score = score

    if best_score != best_possible:
        raise ValueError('the corners provided could not all be mapped to a box corner - are there duplicates present?')

    for i, j in enumerate(best_permutation):
        tmp[j][1] = corners[i]

    first_index = next(i for i in range(4) if tmp[i][1] is not None)
    if len(corners) == 1:
        for i in range(3):
            prior_idx = (first_index + i) % 4
            cur_idx = (prior_idx + 1) % 4
            # tmp[cur_idx][1] = tmp[prior_idx][1].rotate(90)
            tmp[cur_idx][1] = tmp[prior_idx][1].reflect(tmp[prior_idx][0][1])
    else:
        for i in range(3):
            prior_idx = (first_index + i) % 4
            cur_idx = (prior_idx + 1) % 4
            next_idx = (cur_idx + 1) % 4

            if tmp[cur_idx][1] is not None:
                continue

            if tmp[next_idx][1] is None:
                tmp[cur_idx][1] = tmp[prior_idx][1].rotate(90)
                continue

            # Sequence is:
            #
            #   E, S -> S, W
            #   S, W -> W, N
            #   W, N -> N, E
            #   N, E -> E, S

            ds1 = _get_direction_styles(tmp[prior_idx][1], tmp[prior_idx][0][0])
            ds1 = ds1[0].rotate(180)

            ds2 = _get_direction_styles(tmp[next_idx][1], tmp[next_idx][0][1])
            ds2 = ds2[0].rotate(180)

            tmp[cur_idx][1] = BoxDrawingChar.from_direction_styles(ds1, ds2, fuzzy=True)

    sides: typing.List[BoxDrawingChar] = []
    for i in range(0, 4):
        ds1 = _get_direction_styles(tmp[i][1], tmp[i][0][0])
        ds1 = ds1[0].rotate(180)

        j = (i + 1) % 4

        ds2 = _get_direction_styles(tmp[j][1], tmp[j][0][1])
        ds2 = ds2[0].rotate(180)

        sides.append(BoxDrawingChar.from_direction_styles(ds1, ds2, fuzzy=True))

    return Boxer(
        tmp[0][1], sides[0], tmp[1][1],
        sides[3], sides[1],
        tmp[3][1], sides[2], tmp[2][1]
    )
