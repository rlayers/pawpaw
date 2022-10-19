from __future__ import annotations
import typing

import segments


def find_unescaped(
        src: str | segments.Types.C_ITO,
        char: str,
        escape: str = '\\',
        start: int | None = None,
        stop: int | None = None
) -> typing.Iterable[int]:
    if isinstance(src, str):
        s = src
        offset = 0
    elif isinstance(src, segments.Ito):
        s = src.string
        offset = src.start
    else:
        raise segments.Errors.parameter_invalid_type('src', src, str, segments.Ito)

    span = segments.Span.from_indices(src, start, stop).offset(offset)

    if not isinstance(char, str):
        raise segments.Errors.parameter_invalid_type('char', char, str)
    elif len(char) != 1:
        raise ValueError('parameter \'char\' must have length 1')

    if not isinstance(escape, str):
        raise segments.Errors.parameter_invalid_type('escape', escape, str)
    elif len(escape) != 1:
        raise ValueError('parameter \'escape\' must have length 1')

    esc = False
    for i in range(span.start, span.stop):
        c = s[i]
        if esc:
            esc = False
        elif c == escape:
            esc = True
        elif c == char:
            yield i - offset

    if esc:
        raise ValueError('parameter \'src\' ends with un-followed escape char \'{escape}\'')


def split_unescaped(
        src: str | segments.Types.C_ITO,
        char: str,
        escape: str = '\\',
        start: int | None = None,
        stop: int | None = None
) -> typing.Iterable[str] | typing.Iterable[segments.Types.C_ITO]:
    cur = 0
    for i in find_unescaped(src, char, escape, start, stop):
        yield src[cur:i]
        cur = i + 1
    yield src[cur:]
