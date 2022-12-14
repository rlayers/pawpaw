from __future__ import annotations
import typing

import pawpaw


# Finds indeces of non-doubled escape chars
def find_escapes(
    src: str | pawpaw.Types.C_ITO,
    escape: str = '\\',
    start: int | None = None,
    stop: int | None = None
) -> typing.Iterable[int]:
    if isinstance(src, str):
        s = src
        offset = 0
    elif isinstance(src, pawpaw.Ito):
        s = src.string
        offset = src.start
    else:
        raise pawpaw.Errors.parameter_invalid_type('src', src, str, pawpaw.Ito)

    span = pawpaw.Span.from_indices(src, start, stop).offset(offset)

    if not isinstance(escape, str):
        raise pawpaw.Errors.parameter_invalid_type('escape', escape, str)
    elif len(escape) != 1:
        raise ValueError('parameter \'escape\' must have length 1')

    esc = False
    for i in range(span.start, span.stop):
        c = s[i]
        if c == escape:
            esc = not esc
        elif esc:
            yield i - 1
            esc = False


def find_unescaped(
    src: str | pawpaw.Types.C_ITO,
    chars: str,
    escape: str = '\\',
    start: int | None = None,
    stop: int | None = None
) -> typing.Iterable[int]:
    if isinstance(src, str):
        s = src
        offset = 0
    elif isinstance(src, pawpaw.Ito):
        s = src.string
        offset = src.start
    else:
        raise pawpaw.Errors.parameter_invalid_type('src', src, str, pawpaw.Ito)

    span = pawpaw.Span.from_indices(src, start, stop).offset(offset)

    if not isinstance(chars, str):
        raise pawpaw.Errors.parameter_invalid_type('chars', chars, str)
    elif len(chars) == 0:
        raise ValueError('parameter \'chars\' must have non-zero length')

    if not isinstance(escape, str):
        raise pawpaw.Errors.parameter_invalid_type('escape', escape, str)
    elif len(escape) != 1:
        raise ValueError('parameter \'escape\' must have length 1')

    esc = False
    for i in range(span.start, span.stop):
        c = s[i]
        if esc:
            esc = False
        elif c == escape:
            esc = True
        elif c in chars:
            yield i - offset

    if esc:
        raise ValueError('parameter \'src\' ends with un-followed escape char \'{escape}\'')


def split_unescaped(
    src: str | pawpaw.Types.C_ITO,
    char: str,
    escape: str = '\\',
    start: int | None = None,
    stop: int | None = None
) -> typing.Iterable[str] | typing.Iterable[pawpaw.Types.C_ITO]:
    cur = 0
    for i in find_unescaped(src, char, escape, start, stop):
        yield src[cur:i]
        cur = i + 1
    yield src[cur:]
