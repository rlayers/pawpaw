from __future__ import annotations
from dataclasses import dataclass, field
import inspect
import typing
import types


@dataclass(init=False)
class TypeSig:
    ret_val: type = field(default_factory=lambda: [types.NoneType])
    params: typing.List[typing.Type] = field(default_factory=lambda: [])
  
    def __init__(self, rv: type, *params: type):
        self.ret_val = rv
        self.params = [*params]
    

def type_matches_annotation(_type: typing.Type, annotation: typing.Type) -> bool:
    if annotation == inspect._empty:
        return True
        
    if _type == annotation:
        return True
        
    origin = typing.get_origin(annotation)
    if origin is types.UnionType:
        return _type in typing.get_args(annotation)
    elif issubclass(_type, annotation):
        return True
        
    return False


def is_callable(func: typing.Any, ts: TypeSig) -> bool:
    if not isinstance(func, typing.Callable):
        return False
        
    func_sig = inspect.signature(func)
    if not type_matches_annotation(ts.ret_val, func_sig.return_annotation):
        return False
        
    if len(ts.params) != len(func_sig.parameters):
        return False
        
    if not all(type_matches_annotation(tsp, fsp.annotation) for tsp, fsp in zip(ts.params, func_sig.parameters.values())):
        return False
        
    return True
