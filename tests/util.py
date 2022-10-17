import collections.abc
import random
import typing
from unittest import TestCase

import regex
from segments import Span, Ito, Types


class _TestIto(TestCase):
    class IntIto(Ito):  # Used for derived class tests
        def value(self) -> typing.Any:
            return int(self.__str__())
    
    @classmethod
    def add_chars_as_children(cls, ito: Types.C, desc: str | None) -> None:
        ito.children.add(*(ito.clone(i, i + 1, desc) for i in range(*ito.span)))

    def matches_equal(self, first: regex.Match, second: regex.Match, msg: typing.Any = ...) -> None:
        if first is second:
            return
        
        self.assertListEqual([*first.regs], [*second.regs])
        self.assertEqual(first.group(0), second.group(0))
        self.assertSequenceEqual(first.groupdict().keys(), second.groupdict().keys())
        for v1, v2 in zip(first.groupdict().values(), second.groupdict().values()):
            self.assertEqual(v1, v2)
            
    def setUp(self) -> None:
        self.addTypeEqualityFunc(regex.Match, self.matches_equal)

        
class RandSpans:
    def __init__(
            self,
            size: Span = (1, 1),
            gap: Span = (0, 0),
    ):
        if not (isinstance(size, tuple) and len(size) == 2 and all(isinstance(i, int) for i in size)):
            raise TypeError('invalid \'size\'')
        if size[0] < 0 or size[1] < 1 or size[0] > size[1]:
            raise ValueError('invalid \'size\'')
        self.size = size

        if not (isinstance(gap, tuple) and len(gap) == 2 and all(isinstance(i, int) for i in gap)):
            raise TypeError('invalid \'gap\'')
        if (gap[0] < 0 and abs(gap[0]) >= size[0]) or (gap[1] < 0 and abs(gap[1]) >= size[0]):
            raise ValueError('invalid \'gap\'')
        self.gap = gap

    def generate(self, basis: int | collections.abc.Sized, start: int | None = None, stop: int | None = None) -> typing.Iterable[Span]:
        i, stop = Span.from_indices(basis, start, stop)
        while i < stop:
            k = i + random.randint(*self.size)
            k = min(k, stop)
            yield i, k
            if k == stop:
                break
            i = k + random.randint(*self.gap)


class RandSubstrings(RandSpans):
    def __init__(
            self,
            size: Span = Span(1, 1),
            gap: Span = Span(0, 0),
    ):
        super().__init__(size, gap)

    def generate(self, string: str, start: int | None = None, stop: int | None = None) -> typing.Iterable[str]:
        for span in super().generate(string, start, stop):
            yield string[slice(*span)]
