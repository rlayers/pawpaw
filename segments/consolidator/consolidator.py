from abc import ABC, abstractmethod
import typing

from segments import Ito, Types
from segments.errors import Errors


# TODO : output streams could be identities, clones, or something new compared to incoming itos.  So for each chunk,
# do something like:
#
#   for i in incoming:
#       parent = i.parent  # First parent of chunk should be same as subsequents...
#       parent.children.remove(i)
#
#   parent.children.add(*outgoing)


class ConsolidatorEx(ABC):
    @abstractmethod
    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        ...
        
        
class WindowedJoinEx(Consolidator):
    F_SQ_ITOS_2_B = typing.Callable[[Types.C_SQ_ITOS], bool]
    
    def __init__(self, window_size: int, predicate: F_SQ_ITOS_2_B, desc: str | None = None):
        super().__init__()
        
        if not isinstance(window_size, int):
            raise Errors.parameter_invalid_type('window_size', window_size, int)
        if window_size < 2:
            raise ValueError(f'parameter \'window_size\' has value {window_size:,}, but must be greater than or equal to 2')
        self.window_size = window_size

        if not Types.is_callable(predicate, self.F_SQ_ITOS_2_B):
            raise Errors.parameter_invalid_type('predicate', predicate, self.F_SQ_ITOS_2_B)
        self.predicate = predicate

        self.desc = desc

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
        joined: Types.C_ITO | None = None
        window: typing.List[Types.C_ITO] = []
        for ito in itos:
            window.append(ito)
            if len(window) == self.window_size:  # Only when window is full?
                if self.predicate(window):
                    cur = ito.join(window, desc=self.desc)
                    if window[0] is joined:
                        del window[0]
                    yield from (Types.C_BITO(False, i) for i in window)
                    window.clear()
                    window.append(cur)
                    joined = cur
                else:
                    yield Types.C_BITO(False, window.pop(0))

        yield from (Types.C_BITO(False, i) for i in window)

        
class Consolidator(ABC):
    @abstractmethod
    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        ...


class WindowedJoin(Consolidator):
    F_SQ_ITOS_2_B = typing.Callable[[Types.C_SQ_ITOS], bool]
    
    def __init__(self, window_size: int, predicate: F_SQ_ITOS_2_B, desc: str | None = None):
        super().__init__()
        
        if not isinstance(window_size, int):
            raise Errors.parameter_invalid_type('window_size', window_size, int)
        if window_size < 2:
            raise ValueError(f'parameter \'window_size\' has value {window_size:,}, but must be greater than or equal to 2')
        self.window_size = window_size

        if not Types.is_callable(predicate, self.F_SQ_ITOS_2_B):
            raise Errors.parameter_invalid_type('predicate', predicate, self.F_SQ_ITOS_2_B)
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
    F_SQ_ITOS_2_ITO = typing.Callable[[Types.C_SQ_ITOS], Types.C_ITO]
    F_SQ_ITOS_ITO_2_B = typing.Callable[[Types.C_SQ_ITOS, Types.C_ITO], bool]
    
    def __init__(
            self,
            reduce_func: F_SQ_ITOS_2_ITO,
            push_predicate: Types.F_ITO_2_B,
            pop_predicate: F_SQ_ITOS_ITO_2_B | None = None
    ):
        super().__init__()
        if not Types.is_callable(reduce_func, F_SQ_ITOS_2_ITO):
            raise Errors.parameter_invalid_type('reduce_func', reduce_func, self.F_SQ_ITOS_2_ITO)
        self.reduce_func = reduce_func

        if not Types.is_callable(push_predicate, Types.F_ITO_2_B):
            raise Errors.parameter_invalid_type('push_predicate', push_predicate, Types.F_ITO_2_B)
        self.push_predicate = push_predicate

        if pop_predicate is None or Types.is_callable(pop_predicate, self.F_SQ_ITOS_ITO_2_B):
            self.pop_predicate = pop_predicate
        else:
            raise Errors.parameter_invalid_type('pop_predicate', pop_predicate, self.F_SQ_ITOS_ITO_2_B, None)

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


class PromoteChildren(Consolidator):
    def __init__(self, predicate: Types.F_ITO_2_B):
        super().__init__()
        if not Types.is_callable(predicate, Types.F_ITO_2_B):
            raise Errors.parameter_invalid_type('predicate', predicate, Types.F_ITO_2_B)
        self.predicate = predicate

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        stack: typing.List[Ito] = []

        for ito in itos:
            if self.predicate(ito):
                stack.extend(ito.children)
            else:
                stack.append(ito)

        yield from stack
