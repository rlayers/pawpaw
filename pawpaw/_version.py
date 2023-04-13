from __future__ import annotations

import string
import typing

__version__ = '1.0.0.rc1'
"""The str literal that build, setup, documentation, and other tools typically want.
See https://peps.python.org/pep-0440/ for recommended module versioning schema.
"""

class _Segment(typing.NamedTuple):
    value: int
    decorator: str | None

    def __str__(self) -> str:
        return f'{self.value}'

class _PrefixedSegment(_Segment):
    def __str__(self) -> str:
        return self.decorator + super().__str__()

class _SuffixedSegment(_Segment):
    def __str__(self) -> str:
        return super().__str__() + self.decorator

def to_segment(segment: str) -> _Segment:
        if segment.isnumeric():
            return _Segment(int(segment), None)

        lstrp = segment.lstrip(string.ascii_lowercase)
        if (d := len(segment) - len(lstrp)) != 0:
            return _PrefixedSegment(int(lstrp), segment[:d])

        rstrp = segment.rstrip(string.ascii_lowercase)
        d = len(segment) - len(rstrp)
        return _SuffixedSegment(int(rstrp), segment[-d:])

class _Version(typing.NamedTuple):
    segments: tuple[_Segment]

    @classmethod
    def from_(cls, version: str) -> _Version:
        segments = tuple(to_segment(s) for s in version.split('.'))
        return cls(segments)

    def __str__(self) -> str:
        return '.'.join(str(s) for s in self.segments)

Version = _Version.from_(__version__)
