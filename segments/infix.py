"""Infix operator class recipe from https://code.activestate.com/recipes/384122

Returns:
    An infix that can be called using either:
    
        x |op| y
        or
        x <<op>> y
"""
class Infix:
    def __init__(self, function):
        self.function = function
    def __ror__(self, other):
        return Infix(lambda x: self.function(other, x))
    def __or__(self, other):
        return self.function(other)    def __rlshift__(self, other):
        return Infix(lambda x, self=self, other=other: self.function(other, x))
    def __rshift__(self, other):
        return self.function(other)
    def __call__(self, value1, value2):
        return self.function(value1, value2)
