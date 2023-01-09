from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
import typing

from pawpaw import Errors, Ito, Types, nuco

# See 
# 1. https://en.wikipedia.org/wiki/Box-drawing_character
# 2. https://www.unicode.org/charts/PDF/U2500.pdf

class Direction(Enum):
    NW = auto()
    N = auto()
    NE = auto()
    E = auto()
    W = auto()
    SW = auto()
    S = auto()
    SE = auto()

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
        sorted_dss = cls._sort(*direction_styles)
        best_score: int = -1
        best_bdc: BoxDrawingChar
        for instance in filter(lambda i: len(i._direction_styles) == len(direction_styles), cls._instances):
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
    def direction_styles(self) -> str:
        return self._direction_styles

    def __str__(self):
        return self._char


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

    def _from_lines(self, *lines: Types.C_ITO) -> typing.List[str]:
        max_line = max(len(line) for line in lines)

        rv = [f'{self.nw}{str(self.n) * (max_line + 2)}{self.ne}']

        for line in lines:
            rv.append(f'{self.w} {str(line):^{max_line}} {self.e}')

        rv.append(f'{self.sw}{str(self.s) * (max_line + 2)}{self.se}')

        return rv

    def from_srcs(self, *srcs: Types.C_ITO | str) -> typing.List[str]:
        lines: typing.List[Types.C_ITO] = []
        for src in srcs:
            if isinstance(src, str):
                src = Ito(src)
            elif not isinstance(src, Types.C_ITO):
                raise Errors.parameter_invalid_type('srcs', src, ITO, str)
            lines.extend(src.str_splitlines())

        return self._from_lines(*lines)


def from_corners(*corners: BoxDrawingChar) -> Boxer:
    if len(corners) == 0:
        raise ValueError('at least one corner is required')
    elif len(corners) > 4:
        raise ValueError('more than four corners were supplied')

    NW, NE, SE, SW = (0, 1, 2, 3)

    def corner_index(corner: BoxDrawingChar) -> int | None:
        if len(corner.direction_styles) != 2:
            return None

        if corner.direction_styles[0].direction == Direction.N:
            if corner.direction_styles[1].direction == Direction.E:
                return SW
            elif corner.direction_styles[1].direction == Direction.W:
                return SE
        elif corner.direction_styles[1].direction == Direction.S:
            if corner.direction_styles[0].direction == Direction.E:
                return NW
            elif corner.direction_styles[0].direction == Direction.W:
                return NE

        return None

    tmp: typing.List[BoxDrawingChar] = [None, None, None, None]
    for corner in corners:
        i = corner_index(corner)
        if i is None:
            raise ValueError(f'\'{corner}\' is not a box drawing character corner')
        else:
            tmp[i] = corner
    corners = tmp

    def prior_idx(i: int) -> int:
        return (i + 3) % 4
    
    def next_idx(i: int) -> int:
        return (i + 1) % 4

    start = next(i for i in range(4) if corners[i] is not None)
    start = next_idx(start)
    for j in range(3):
        i = (start + j) % 4

        if corners[i] is not None:
            continue

        prior = corners[prior_idx(i)]
        next_ = corners[next_idx(i)]

        if i == NW:
            ds1 = DirectionStyle(Direction.S, prior.direction_styles[0].style)
            style = prior.direction_styles[1].style if next_ is None else next_.direction_styles[0].style
            ds2 = DirectionStyle(Direction.E, style)
        elif i == NE:
            ds1 = DirectionStyle(Direction.W, prior.direction_styles[0].style)
            style = prior.direction_styles[0].style if next_ is None else next_.direction_styles[0].style
            ds2 = DirectionStyle(Direction.S, style)
        elif i == SE:
            ds1 = DirectionStyle(Direction.N, prior.direction_styles[1].style)
            style = prior.direction_styles[0].style if next_ is None else next_.direction_styles[1].style
            ds2 = DirectionStyle(Direction.W, style)
        else:  # SW:
            ds1 = DirectionStyle(Direction.E, prior.direction_styles[1].style)
            style = prior.direction_styles[1].style if next_ is None else next_.direction_styles[1].style
            ds2 = DirectionStyle(Direction.N, style)

        corners[i] = BoxDrawingChar.from_direction_styles(ds1, ds2, fuzzy=True)

    ds1 = DirectionStyle(Direction.W, corners[NW].direction_styles[0].style)
    ds2 = DirectionStyle(Direction.E, corners[NE].direction_styles[0].style)
    top = BoxDrawingChar.from_direction_styles(ds1, ds2, fuzzy=True)

    ds1 = DirectionStyle(Direction.N, corners[NW].direction_styles[1].style)
    ds2 = DirectionStyle(Direction.S, corners[SW].direction_styles[0].style)
    left = BoxDrawingChar.from_direction_styles(ds1, ds2, fuzzy=True)

    ds1 = DirectionStyle(Direction.N, corners[NE].direction_styles[1].style)
    ds2 = DirectionStyle(Direction.S, corners[SE].direction_styles[0].style)
    right = BoxDrawingChar.from_direction_styles(ds1, ds2, fuzzy=True)

    ds1 = DirectionStyle(Direction.W, corners[SW].direction_styles[1].style)
    ds2 = DirectionStyle(Direction.E, corners[SE].direction_styles[1].style)
    bottom = BoxDrawingChar.from_direction_styles(ds1, ds2, fuzzy=True)

    return Boxer(
        corners[NW], top, corners[NE],
        left, right,
        corners[SW], bottom, corners[SE]
    )
