from typing import Any, NewType

class staticproperty(property):
    """Utilidad para crear propiedades estáticas (que no tomen el puntero a self)"""

    def __get__(self, cls, owner):
        return staticmethod(self.fget).__get__(None, owner)()
    
class classproperty(property):
    """Utilidad para crear propiedades de clase"""

    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()

class Workflow:
    class action:
        def __class_getitem__(cls, x):
            return (cls, x)
    
    __actions__: dict[str, callable] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__actions__ = cls.__actions__.copy()

        for k,v in cls.__annotations__.items():
            if isinstance(v, tuple) and len(v) == 2:
                t, f = v
                if isinstance(t, type) and t == Workflow.action:
                    cls.__actions__[k] = f

        for a in cls.__actions__:
            del cls.__annotations__[a]


    @classproperty
    def start(cls):
        return cls()

    def __getattribute__(self, __name: str) -> Any:
        return type(self).__actions__[__name]
    
action = Workflow.action

# Usage: 
#
# def foo(*xs):
#     return xs
#
# class test(Workflow):
#     f: action[foo]
#     g: action[lambda x: x+1]
#
# test.start.g(1)
