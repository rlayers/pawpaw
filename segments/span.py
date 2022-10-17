from __future__ import annotations
import collections.abc
import types
import typing

from segments.errors import Errors


class Span(typing.NamedTuple):
    start: int
    stop: int
        
    @classmethod
    def from_indices(
        cls,
        basis: int | collections.abc.Sized,
        start: int | None = None,
        stop: int | None = None
    ) -> Span:
        if isinstance(basis, int):
            length = basis
        elif isinstance(basis, collections.abc.Sized):
            length = len(basis)
        else:
            raise Errors.parameter_invalid_type('basis', basis, int, collections.abc.Sized)

        if start is None:
            start = 0
        elif not isinstance(start, int):
            raise Errors.parameter_invalid_type('start', start, int, types.NoneType)
        else:
            start = min(length, start) if start >= 0 else max(0, length + start)

        if stop is None:
            stop = length
        elif not isinstance(stop, int):
            raise Errors.parameter_invalid_type('stop', stop, int, types.NoneType)
        else:
            stop = min(length, stop) if stop >= 0 else max(0, length + stop)
            
        stop = max(start, stop)

        return Span(start, stop)

    def offset(self, i: int) -> Span:
        if not isinstance(i, int):
            raise Errors.parameter_invalid_type('i', i, int)
            
        if i == 0:
            return self
        
        rv = Span(self.start + i, self.stop + i)
        if rv.start < 0 or rv.stop < 0:
            raise ValueError(f'offsetting by {i:,} results in negative indices')
        
        return rv
