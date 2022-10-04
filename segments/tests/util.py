import collections
import random
import typing
from unittest import TestCase

from segments import Span, Ito, slice_indices_to_span


class _TestIto(TestCase):
    @classmethod
    def add_chars_as_children(cls, ito: Ito, descriptor: str | None) -> None:
        ito.children.add(*(ito.clone(i, i + 1, descriptor) for i in range(*ito.span)))
        # for i in range(*ito.span):
        #     ito.children.add(ito.clone(i, i+1, descriptor))

    def assertEqual(self, first: typing.Any, second: typing.Any, msg: typing.Any = ...) -> None:
        if isinstance(first, Ito) and isinstance(second, Ito):
            self.assertEqual(first.string, second.string, msg)
            self.assertEqual(first.span, second.span, msg)
            self.assertEqual(first.descriptor, second.descriptor, msg)
            self.assertIs(first.value_func, second.value_func, msg)
        else:
            TestCase.assertEqual(self, first, second, msg)


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
        i, stop = slice_indices_to_span(basis, start, stop)
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
            size: Span = (1, 1),
            gap: Span = (0, 0),
    ):
        super().__init__(size, gap)

    def generate(self, string: str, start: int | None = None, stop: int | None = None) -> typing.Iterable[str]:
        for span in super().generate(string, start, stop):
            yield string[slice(*span)]