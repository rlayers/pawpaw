from __future__ import annotations
import typing

import pawpaw


# Finds indices of non-doubled escape chars
def find_escapes(
    src: str | pawpaw.Ito,
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
    src: str | pawpaw.Ito,
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
    src: str | pawpaw.Ito,
    char: str,
    escape: str = '\\',
    start: int | None = None,
    stop: int | None = None
) -> typing.Iterable[str] | typing.Iterable[pawpaw.Ito]:
    cur = 0
    for i in find_unescaped(src, char, escape, start, stop):
        yield src[cur:i]
        cur = i + 1
    yield src[cur:]


def find_balanced(
    src: str | pawpaw.Ito,
    lchar: str | pawpaw.Ito,
    rchar: str | pawpaw.Ito,
    escape: str = '\\',
    start: int | None = None,
    stop: int | None = None
) -> typing.Iterable[str] | typing.Iterable[pawpaw.Ito]:
    if isinstance(src, str):
        s = src
        offset = 0
    elif isinstance(src, pawpaw.Ito):
        s = src.string
        offset = src.start
    else:
        raise pawpaw.Errors.parameter_invalid_type('src', src, str, pawpaw.Ito)

    if not (isinstance(lchar, str) or isinstance(lchar, pawpaw.Ito)):
        raise pawpaw.Errors.parameter_invalid_type('left', lchar, str, pawpaw.Ito)
    elif len(lchar) != 1:
        raise ValueError('parameter \'left\' must have length 1')
    lchar = str(lchar)

    if not (isinstance(rchar, str) or isinstance(rchar, pawpaw.Ito)):
        raise pawpaw.Errors.parameter_invalid_type('right', rchar, str, pawpaw.Ito)
    elif len(rchar) != 1:
        raise ValueError('parameter \'right\' must have length 1')
    rchar = str(rchar)

    lefts = []
    for i in find_unescaped(src, lchar + rchar, escape, start, stop):
        c = s[offset + i]
        if c == lchar and (lchar != rchar or len(lefts) == 0):
            lefts.append(i)
        else:
            len_lefts = len(lefts)
            if len_lefts > 1:
                lefts.pop()
            elif len_lefts == 1:
                yield src[lefts.pop():i+1]
            else:
                raise ValueError(f'unbalanced right char {rchar} found at index {i}')
        
    if len(lefts) != 0:
        raise ValueError(f'unbalanced left char {lchar} found at index {lefts.pop()}')
