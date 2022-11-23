from dataclasses import dataclass


# See https://en.wikipedia.org/wiki/Box-drawing_character

@dataclass(frozen=True)
class _Line:
    SINGLE_LIGHT: str
    SINGLE_HEAVY: str
    DOUBLE: str
    DOUBLE_DASH_LIGHT: str
    DOUBLE_DASH_HEAVY: str
    QUADRUPLE_DASH_LIGHT: str
    QUADRUPLE_DASH_HEAVY: str
    TRIPLE_DASH_LIGHT: str
    TRIPLE_DASH_HEAVY: str


@dataclass(frozen=True)
class _Lines:
    Horizontal = _Line(
        SINGLE_LIGHT='─',
        SINGLE_HEAVY='━',
        DOUBLE='═',
        DOUBLE_DASH_LIGHT='╌',
        DOUBLE_DASH_HEAVY='╍',
        QUADRUPLE_DASH_LIGHT='┈',
        QUADRUPLE_DASH_HEAVY='┉',
        TRIPLE_DASH_LIGHT='┄',
        TRIPLE_DASH_HEAVY='┅',
    )
    Vertical = _Line(
        SINGLE_LIGHT='│',
        SINGLE_HEAVY='┃',
        DOUBLE='║',
        DOUBLE_DASH_LIGHT='╎',
        DOUBLE_DASH_HEAVY='╏',
        QUADRUPLE_DASH_LIGHT='┊',
        QUADRUPLE_DASH_HEAVY='┋',
        TRIPLE_DASH_LIGHT='┆',
        TRIPLE_DASH_HEAVY='┇',
    )


Lines = _Lines()


@dataclass(frozen=True)
class _Corner:
    HZ_LIGHT_VT_LIGHT: str
    HZ_LIGHT_VT_HEAVY: str
    HZ_HEAVY_VT_LIGHT: str
    HZ_HEAVY_VT_HEAVY: str
    HZ_LIGHT_VT_DOUBLE: str
    HZ_DOUBLE_VT_LIGHT: str
    HZ_DOUBLE_VT_DOUBLE: str


@dataclass(frozen=True)
class _Corners:
    NE = _Corner(
        HZ_LIGHT_VT_LIGHT='┐',
        HZ_LIGHT_VT_HEAVY='┒',
        HZ_HEAVY_VT_LIGHT='┑',
        HZ_HEAVY_VT_HEAVY='┓',
        HZ_LIGHT_VT_DOUBLE='╖',
        HZ_DOUBLE_VT_LIGHT='╕',
        HZ_DOUBLE_VT_DOUBLE='╗',
    )
    SE = _Corner(
        HZ_LIGHT_VT_LIGHT='┘',
        HZ_LIGHT_VT_HEAVY='┚',
        HZ_HEAVY_VT_LIGHT='┙',
        HZ_HEAVY_VT_HEAVY='┛',
        HZ_LIGHT_VT_DOUBLE='╜',
        HZ_DOUBLE_VT_LIGHT='╛',
        HZ_DOUBLE_VT_DOUBLE='╝',
    )
    SW = _Corner(
        HZ_LIGHT_VT_LIGHT='└',
        HZ_LIGHT_VT_HEAVY='┖',
        HZ_HEAVY_VT_LIGHT='┕',
        HZ_HEAVY_VT_HEAVY='┗',
        HZ_LIGHT_VT_DOUBLE='╙',
        HZ_DOUBLE_VT_LIGHT='╘',
        HZ_DOUBLE_VT_DOUBLE='╚',
    )
    NW = _Corner(
        HZ_LIGHT_VT_LIGHT='┌',
        HZ_LIGHT_VT_HEAVY='┎',
        HZ_HEAVY_VT_LIGHT='┍',
        HZ_HEAVY_VT_HEAVY='┏',
        HZ_LIGHT_VT_DOUBLE='╓',
        HZ_DOUBLE_VT_LIGHT='╒',
        HZ_DOUBLE_VT_DOUBLE='╔',
    )


Corners = _Corners()
    