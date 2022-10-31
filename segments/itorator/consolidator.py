from abc import ABC, abstractmethod
import typing

from segments import Ito, Types
from segments.errors import Errors


class Consolidator(ABC):
    @abstractmethod
    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        pass


class Merge(Consolidator):
    def __init__(
            self,
            window_size: int,
            predicate: typing.Callable[[typing.List[Types.C_ITO]], bool],
            desc: str | None = None
    ):
        super().__init__()
        if not isinstance(window_size, int):
            raise Errors.parameter_invalid_type('window_size', window_size, int)
        if window_size < 2:
            raise ValueError(f'parameter \'window_size\' has value {window_size:,}, but must be greater than or equal to 2')
        self.window_size = window_size

        if not isinstance(predicate, typing.Callable):
            raise Errors.parameter_invalid_type('predicate', predicate, typing.Callable[[typing.List[Types.C_ITO]], bool])
        self.predicate = predicate

        self.desc = desc

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        window: typing.List[Types.C_ITO] = []
        for ito in itos:
            window.append(ito)
            if len(window) == self.window_size:
                if self.predicate(window):
                    window.append(ito.join(window, desc=self.desc))
                    del window[:-1]
                else:
                    yield window.pop(0)

        yield from window


class Reduce(Consolidator):
    def __init__(
            self,
            reduce_func: typing.Callable[[typing.List[Ito]], Ito],
            push_predicate: typing.Callable[[Ito], bool],
            pop_predicate: typing.Callable[[typing.List[Ito], Ito], bool] | None = None
    ):
        super().__init__()
        if not isinstance(reduce_func, typing.Callable):
            raise Errors.parameter_invalid_type('reduce_func', reduce_func, typing.Callable)
        self.reduce_func = reduce_func

        if not isinstance(push_predicate, typing.Callable):
            raise Errors.parameter_invalid_type('push_predicate', push_predicate, typing.Callable)
        self.push_predicate = push_predicate

        if pop_predicate is None or isinstance(pop_predicate, typing.Callable):
            self.pop_predicate = pop_predicate
        else:
            raise Errors.parameter_invalid_type('pop_predicate', pop_predicate, typing.Callable)

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        stack: typing.List[Ito] = []
        for ito in itos:
            if stack:
                if self.pop_predicate is not None and self.pop_predicate(stack, ito):
                    yield self.reduce_func(stack)
                    stack.clear()
                else:
                    stack.append(ito)

            if not stack:
                if self.push_predicate(ito):
                    stack.append(ito)
                else:
                    yield ito

        if stack:
            yield self.reduce_func(stack)


class Reclaim(Consolidator):
    """
    Allocate span regions not assigned to children
    """
    def __init__(
            self,
            desc_func: typing.Callable[[int, int], str] = lambda span: None,
            trim_and_filter_ws: bool = False
    ):
        super().__init__()
        if not isinstance(desc_func, typing.Callable):
            raise Errors.parameter_invalid_type('desc_func', desc_func, typing.Callable)
        self.desc_func = desc_func

        if not isinstance(trim_and_filter_ws, bool):
            raise Errors.parameter_invalid_type('trim_and_filter_ws', trim_and_filter_ws, bool)
        self.trim_and_filter_ws = trim_and_filter_ws

    # TODO : Check for relative indices and use alt Ito ctor if needed
    # TODO : Change params start & stop to Swap type
    def _append_if(self, parent: Ito, start: int, stop: int) -> None:
        child = parent.clone(start, stop, desc=self.desc_func(start, stop))
        if self.trim_and_filter_ws:
            child = child.str_strip()
            if child.start == child.stop:
                return

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        for ito in itos:
            clone = ito.clone()
            if ito.parent is not None:
                ito.parent.children[ito.parent.children.index(ito)] = clone

            last = ito.start
            while len(ito.children) > 0:
                c = ito.children.pop(0)
                if c.start > last:
                    self._append_if(clone, last, c.start)
                clone.children.add(c)
                last = c.stop

            if last < ito.stop:
                self._append_if(clone, last, ito.stop)

            yield clone


class PromoteChildren(Consolidator):
    def __init__(self, predicate: typing.Callable[[Ito], bool]):
        super().__init__()
        if not isinstance(predicate, typing.Callable):
            raise Errors.parameter_invalid_type('predicate', predicate, typing.Callable)
        self.predicate = predicate

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        stack: typing.List[Ito] = []

        for ito in itos:
            if self.predicate(ito):
                stack.extend(ito.children)
            else:
                stack.append(ito)

        yield from stack
