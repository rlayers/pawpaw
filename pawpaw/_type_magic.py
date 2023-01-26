from __future__ import annotations
import inspect
import types
import typing

from pawpaw.errors import Errors


CALLABLE_TYPE_OR_GENERIC = typing._CallableType | typing._CallableGenericAlias

def is_callable_type_or_generic(obj: typing.Any) -> bool:
    '''
        Returns True if obj is typing._Callable or typing._CallableGenericAlias
    '''
    return isinstance(obj, CALLABLE_TYPE_OR_GENERIC)


def is_functoid(obj: typing.Any):
    '''
    Python's builtin callable method' returns true for all callable types (e.g., def, lambda,
    instance/class/builtin method, etc.) However, it also returns True for typing.Callable
    objects.  E.g.:

    >>> MY_FUNC_ALIAS = typing.Callable[[int], str]
    >>> callable(MY_FUNC_ALIAS)
    True

    This method returns False in such cases

    The terms 'Function', 'Method', 'Callable', etc. all have established meanings in Python.
    It would be confusing to label this method 'callable', and the terms 'Function', 'Method',
    etc. already have established meantings in pythong.  So instead, I'm using 'functoid'
    '''
    return callable(obj) and not is_callable_type_or_generic(obj)


_LAMBDA_OBJ_NAME = (lambda: True).__name__  # Use this instead of string literal in case Python changes


# Note: Guido van Rossum uses 'def' and 'lambda' for these two concepts (see:
# https://stackoverflow.com/questions/62479608/lambdatype-vs-functiontype), so I'll
# use the same naming convention here

def is_def(obj: typing.Any) -> bool:
    '''
        Returns True if obj is def (defined function)
    '''
    return isinstance(obj, types.FunctionType) and obj.__name__ != _LAMBDA_OBJ_NAME


def is_lambda(obj: typing.Any) -> bool:
    '''
        Returns True if obj is lambda
    '''
    return isinstance(obj, types.FunctionType) and obj.__name__ == _LAMBDA_OBJ_NAME


TYPE_OR_UNION = typing.Type | types.UnionType


def unpack(t: TYPE_OR_UNION) -> typing.List[type]:
    rv = list[typing.Type]()
    
    if (origin := typing.get_origin(t)) is types.UnionType:
        for i in typing.get_args(t):
            rv.extend(unpack(i))
    else:
        rv.append(t)

    return rv


def isinstance_ex(obj: object, type_or_union: TYPE_OR_UNION) -> bool:
    '''
    Although Python >= 3.10 now allows Union as 2nd parameter to isinstance method, it doesn't
    allow _parameterized_ types.  This function performs weak checking for any supplied
    parameterized types.

    Tuples are not allowed for 2nd parameter because... why support them now that you can pass a Union?
    '''
    for t in unpack(type_or_union):
        if (origin := typing.get_origin) is not None:
            # Could expand this for various generic types
            if isinstance(obj, origin):
                return True
        elif issubclass(obj, t):
            return True
    return False


class Functoid:
    """Marker object"""


def functoid_isinstance(functoid: typing.Callable, callable_type_or_generic: CALLABLE_TYPE_OR_GENERIC) -> bool:
    '''
    There is no good way to type hint for functoid, so falling back to 'typing.Callable'
    '''
    if not is_functoid(functoid):
        raise Errors.parameter_invalid_type('functoid', functoid, Functoid)

    # This has guarranteed entries for the ret_val and all params, however, the types _may_ be
    # strings if "from __future__ import annotations" is used.
    func_sig_2 = inspect.signature(func)

    # This has proper types, even when "from __future__ import annotations" used.  However:
    # if the ret-val or param lacks a type hint, it is missing from this dict
    func_sig_1 = typing.get_type_hints(func)

    ts_params, ts_ret_val = typing.get_args(callable_type_or_generic)


# def issubclass(cls: TYPE_OR_UNION, template: TYPE_OR_UNION):
#     template_Types = as_types(template)



# def type_matches_annotation(t1: TYPE_CHECKABLE, t2: TYPE_CHECKABLE) -> bool:
#     if isinstance(t1, inspect.Signature.empty) or isinstance(t2, inspect.Signature.empty):
#         return True  # Can't check empty

#     ats = _as_types(t2)
#     if len(ats) > 0:  # Impossible to check without
#         for tt in _as_types(t):
#             if not any(issubclass(tt, at) for at in ats):
#                 return False

#     return True





# def _callable_type_checkables(func: typing.Callable) -> tuple(typing.Dict[str, TYPE_CHECKABLE], TYPE_CHECKABLE):
#     # This has proper types, even when "from __future__ import annotations" used.  However:
#     # if the ret-val or param lacks a type hint, it is missing from this dict
#     func_sig_1 = typing.get_type_hints(func)

#     # This has guarranteed entries for the ret_val and all params, however, the types _may_ be
#     # strings if "from __future__ import annotations" is used.
#     func_sig_2 = inspect.signature(func)

#     ts_params, ts_ret_val = typing.get_args(type_sig)




# def is_callable(func: typing.Any, type_sig: typing.Callable) -> bool:
#     if not isinstance(func, typing.Callable):
#         return False

#     ts_params, ts_ret_val = typing.get_args(type_sig)

#     # This has proper types, even when "from __future__ import annotations" used.  However:
#     # if the ret-val or param lacks a type hint, it is missing from this dict
#     func_sig_1 = typing.get_type_hints(func)

#     # This has guarranteed entries for the ret_val and all params, however, the types _may_ be
#     # strings if "from __future__ import annotations" is used.
#     func_sig_2 = inspect.signature(func)

#     # use func_sig_2.return_annotation?
#     if (f_ret_val := func_sig_1.get('return', None)) != None:
#         if not type_checkables_match(ts_ret_val, f_ret_val):
#             return False

#     if len(ts_params) != len(func_sig_2.parameters):
#         return False

#     for tsp, fsp in zip(ts_params, func_sig_2.parameters.values()):
#         if isinstance(fsp.annotation, typing.get_args(TYPE_CHECKABLE)):
#             f_param_val = fsp.annotation
#         else:
#             f_param_val = func_sig_1.get(fsp, None)

#         if f_param_val != None and not type_checkables_match(tsp, f_param_val):
#             return False

#     return True


# def is_desc_func(func: typing.Callable) -> bool:
#     if not isinstance(func, typing.Callable):
#         return False

#     sig = inspect.signature(func)
#     if not type_checkables_match(str, sig.return_annotation):
#         return False

#     return True


# def is_lambda(func: typing.Callable):
#     return type(func) is types.LambdaType and func.__name__ == '<lambda>'


# def invoke_func(func: typing.Any, *vals: typing.Any) -> typing.Any:
#     """Wire and fire

#     Args:
#         func:
#         *vals:

#     Returns:
#         Invokes func and returns its return value
#     """

#     if is_lambda(func):
#         return func(*vals)  # No type hints on lamdbas, so this is the best we can do

#     unpaired: typing.List[typing.Any] = list(vals)

#     arg_spec = inspect.getfullargspec(func)
#     del arg_spec.annotations['return']

#     p_args: typing.List[typing.Any] = []
#     for arg in arg_spec.args:
#         for val in unpaired:
#             val_type = type(val)
#             if type_checkables_match(val_type, arg_spec.annotations[arg]):
#                 p_args.append(val)
#                 unpaired.remove(val)
#                 break

#     p_kwonlyargs: typing.Dict[str, typing.Any] = {}
#     for arg in arg_spec.kwonlyargs:
#         for val in unpaired:
#             val_type = type(val)
#             if type_checkables_match(val_type, arg_spec.annotations[arg]):
#                 p_kwonlyargs[arg] = val
#                 unpaired.remove(val)
#                 break

#     p_vargs: typing.List[typing.Any] = []
#     if len(unpaired) > 0 and arg_spec.varargs is not None:
#         p_vargs[arg_spec.varargs] = unpaired

#     return func(*p_args, *p_vargs, **p_kwonlyargs)
