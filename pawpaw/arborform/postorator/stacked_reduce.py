from abc import ABC, abstractmethod
import typing

from pawpaw import Ito, Types, Errors
from pawpaw.arborform.postorator import Postorator

       
class StackedReduce(Postorator):
    F_SQ_ITOS_2_ITO = typing.Callable[[Types.C_SQ_ITOS], Ito]
    F_SQ_ITOS_ITO_2_B = typing.Callable[[Types.C_SQ_ITOS, Ito], bool]
    
    def __init__(
            self,
            reduce_func: F_SQ_ITOS_2_ITO,
            push_predicate: Types.F_ITO_2_B,
            pop_predicate: F_SQ_ITOS_ITO_2_B | None = None,
            tag: str | None = None
    ):
        super().__init__(tag)
        if not Types.is_callable(reduce_func, self.F_SQ_ITOS_2_ITO):
            raise Errors.parameter_invalid_type('reduce_func', reduce_func, self.F_SQ_ITOS_2_ITO)
        self.reduce_func = reduce_func

        if not Types.is_callable(push_predicate, Types.F_ITO_2_B):
            raise Errors.parameter_invalid_type('push_predicate', push_predicate, Types.F_ITO_2_B)
        self.push_predicate = push_predicate

        if pop_predicate is None or Types.is_callable(pop_predicate, self.F_SQ_ITOS_ITO_2_B):
            self.pop_predicate = pop_predicate
        else:
            raise Errors.parameter_invalid_type('pop_predicate', pop_predicate, self.F_SQ_ITOS_ITO_2_B, None)

    def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_BITOS:
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


# class PromoteChildren(Consolidator):
#     def __init__(self, predicate: Types.F_ITO_2_B):
#         super().__init__()
#         if not Types.is_callable(predicate, Types.F_ITO_2_B):
#             raise Errors.parameter_invalid_type('predicate', predicate, Types.F_ITO_2_B)
#         self.predicate = predicate

#     def traverse(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
#         stack: typing.List[pawpaw.Ito] = []

#         for ito in itos:
#             if self.predicate(ito):
#                 stack.extend(ito.children)
#             else:
#                 stack.append(ito)

#         yield from stack
