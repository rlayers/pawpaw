import typing

from pawpaw import Ito, Types, Errors, type_magic
from pawpaw.arborform.postorator import Postorator

       
class StackedReduce(Postorator):
    F_SQ_ITOS_2_ITO = typing.Callable[[Types.C_SQ_ITOS], Ito]
    P_SQ_ITOS_ITO = typing.Callable[[Types.C_SQ_ITOS, Ito], bool]
    
    def __init__(
            self,
            reduce_func: F_SQ_ITOS_2_ITO,
            push_predicate: Types.P_ITO,
            pop_predicate: P_SQ_ITOS_ITO | None = None,
            tag: str | None = None
    ):
        super().__init__(tag)
        if not type_magic.functoid_isinstance(reduce_func, self.F_SQ_ITOS_2_ITO):
            raise Errors.parameter_invalid_type('reduce_func', reduce_func, self.F_SQ_ITOS_2_ITO)
        self.reduce_func = reduce_func

        if not type_magic.functoid_isinstance(push_predicate, Types.P_ITO):
            raise Errors.parameter_invalid_type('push_predicate', push_predicate, Types.P_ITO)
        self.push_predicate = push_predicate

        if pop_predicate is None or type_magic.functoid_isinstance(pop_predicate, self.P_SQ_ITOS_ITO):
            self.pop_predicate = pop_predicate
        else:
            raise Errors.parameter_invalid_type('pop_predicate', pop_predicate, self.P_SQ_ITOS_ITO, None)

    def _transform(self, itos: Types.C_IT_ITOS) -> Types.C_IT_ITOS:
        stack: typing.List[Ito] = []
        for ito in itos:
            if len(stack) > 0:
                if self.pop_predicate is not None and self.pop_predicate(stack, ito):
                    yield self.reduce_func(stack)
                    stack.clear()
                else:
                    stack.append(ito)

            if len(stack) == 0:
                if self.push_predicate(ito):
                    stack.append(ito)
                else:
                    yield ito

        if len(stack) > 0:
            yield self.reduce_func(stack)
