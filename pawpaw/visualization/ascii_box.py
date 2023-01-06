from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
import typing

from pawpaw import Errors, Ito, Types

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
    def from_direction_styles(cls, *direction_styles: DirectionStyle) -> BoxDrawingChar:
        sorted_dss = cls._sort(*direction_styles)

        for instance in filter(lambda i: len(i._direction_styles) == len(direction_styles), cls._instances):
            if all(s1 == s2 for s1, s2 in zip(sorted_dss, instance._direction_styles)):
                return instance

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
            '─',
            'BOX DRAWINGS LIGHT HORIZONTAL',
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.E, Style()),
        ),

        BoxDrawingChar(
            '│',
            'BOX DRAWINGS LIGHT VERTICAL',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.S, Style()),
        ),

        BoxDrawingChar(
            '└',
            'BOX DRAWINGS LIGHT UP AND RIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style()),
        ),

        BoxDrawingChar(
            '┌',
            'BOX DRAWINGS LIGHT DOWN AND RIGHT',
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),

        BoxDrawingChar(
            '╭',
            'BOX DRAWINGS LIGHT ARC DOWN AND RIGHT',
            DirectionStyle(Direction.E, Style(path=Style.Path.ARC)),
            DirectionStyle(Direction.S, Style(path=Style.Path.ARC)),
        ),        

        BoxDrawingChar(
            '├',
            'BOX DRAWINGS LIGHT VERTICAL AND RIGHT',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.S, Style()),
        ),

        BoxDrawingChar(
            '┼',
            'BOX DRAWINGS LIGHT VERTICAL AND HORIZONTAL',
            DirectionStyle(Direction.N, Style()),
            DirectionStyle(Direction.E, Style()),
            DirectionStyle(Direction.W, Style()),
            DirectionStyle(Direction.S, Style()),
        ),
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

        rv = [f'{self.nw}{self.n * (max_line + 2)}{self.ne}']

        for line in lines:
            rv.append(f'{self.w} {line:^{max_line}} {self.e}')

        rv.append(f'{self.sw}{self.s * (max_line + 2)}{self.se}')

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

def from_corners(
    upper_left: BoxDrawingChar | typing.Tuple[Style, Style] | None = None,
    upper_right: BoxDrawingChar | typing.Tuple[Style, Style] | None = None,
    lower_left: BoxDrawingChar | typing.Tuple[Style, Style] | None = None,
    lower_right: BoxDrawingChar | typing.Tuple[Style, Style] | None = None
) -> Boxer:
    if all(c is None for c in (upper_left, upper_right, lower_left, lower_right)):
        raise ValueError('At least one corner is required')

    if isinstance(upper_left, typing.Tuple(Style, Style)):
        upper_left = BoxDrawingChar.from_direction_styles(DirectionStyle(Direction.E, upper_left[0]), DirectionStyle(Direction.S, upper_left[1]))
    elif isinstance(upper_left, BoxDrawingChar):
        if not (len(upper_left.direction_styles) == 2 and upper_left.direction_styles[0].direction == Direction.E and upper_left.direction_styles[1].direction == Direction.S):
            raise ValueError('parameter \'upper_left\' is not an upper left corner')
    elif upper_left is not None:
        raise Errors.parameter_invalid_type('upper_left', upper_left, BoxDrawingChar, typing.Tuple[Style, Style], None)

    if isinstance(upper_right, typing.Tuple(Style, Style)):
        upper_right = BoxDrawingChar.from_direction_styles(DirectionStyle(Direction.W, upper_right[0]), DirectionStyle(Direction.S, upper_right[1]))
    elif isinstance(upper_right, BoxDrawingChar):
        if not (len(upper_right.direction_styles) == 2 and upper_right.direction_styles[0].direction == Direction.W and upper_right.direction_styles[1].direction == Direction.S):
            raise ValueError('parameter \'upper_right\' is not an upper right corner')
    elif upper_right is not None:
        raise Errors.parameter_invalid_type('upper_right', upper_right, BoxDrawingChar, typing.Tuple[Style, Style], None)

    if isinstance(lower_left, typing.Tuple(Style, Style)):
        lower_left = BoxDrawingChar.from_direction_styles(DirectionStyle(Direction.N, lower_left[0]), DirectionStyle(Direction.E, lower_left[1]))
    elif isinstance(lower_left, BoxDrawingChar):
        if not (len(lower_left.direction_styles) == 2 and lower_left.direction_styles[0].direction == Direction.N and lower_left.direction_styles[1].direction == Direction.E):
            raise ValueError('parameter \'lower_left\' is not a lower left corner')
    elif lower_left is not None:
        raise Errors.parameter_invalid_type('lower_left', lower_left, BoxDrawingChar, typing.Tuple[Style, Style], None)

    if isinstance(lower_right, typing.Tuple(Style, Style)):
        lower_right = BoxDrawingChar.from_direction_styles(DirectionStyle(Direction.N, lower_right[0]), DirectionStyle(Direction.W, lower_right[1]))
    elif isinstance(lower_right, BoxDrawingChar):
        if not (len(lower_right.direction_styles) == 2 and lower_right.direction_styles[0].direction == Direction.N and lower_right.direction_styles[1].direction == Direction.W):
            raise ValueError('parameter \'lower_right\' is not a lower right corner')
    elif lower_right is not None:
        raise Errors.parameter_invalid_type('lower_right', lower_right, BoxDrawingChar, typing.Tuple[Style, Style], None)

    corners = [upper_left, upper_right, lower_left, lower_right]

    def prior_idx(i: int) -> int:
        return (i + 3) % 4
    
    def next_idx(i: int) -> int:
        return (i + 1) % 4

    NW, NE, SE, SW = (0, 1, 2, 3)

    def build_corner(i: int) -> Corner:
        prior = corners[prior_idx(i)]
        next_ = corners[next_idx(i)]
        if prior is None:
            if i == NW:
                ds1, ds2 = DirectionStyle(Direction.E, next(lambda ds: ds.direction == Direction.W, next_.direction_styles))
            elif i == NE:
                ds1, ds2 = DirectionStyle(Direction.S, next(lambda ds: ds.direction == Direction.N, next_.direction_styles))
            elif i == SE:
                ds1, ds2 = DirectionStyle(Direction.W, next(lambda ds: ds.direction == Direction.E, next_.direction_styles))
            else:  # SW:
                ds1, ds2 = DirectionStyle(Direction.N, next(lambda ds: ds.direction == Direction.S, next_.direction_styles))
        elif next is None:
            pass
        else:
            pass

        return BoxDrawingChar.from_direction_styles(ds1, ds2)

    for i in filter(lambda i: corners[i] is None, range(4)):
        corners[i] = build_corner(i)

    top, left, right, bottom = ''  # TODO: Find matches

    return Boxer(
        corners[NW], top, corners[NE],
        left, right,
        corners[SW], bottom, corners[NE]
    )
