import re
import ast
import inspect
from types import NoneType
from typing import TypeVar, Callable
from collections.abc import Iterable


def identity(x): return x
def show(x): 
    print(x)
    return x

def Try(f):
    try:
        return f()
    except Exception as e:
        return e

def longest_lambda_substring(s):
    longest_lambda = ''
    for i in range(len(s), -1, -1):
        for j in range(0, len(s) - i + 1):
            substring = s[j:j+i]
            result = Try(lambda: ast.parse(substring, mode='eval'))
            
            if isinstance(result, Exception):
                continue

            if isinstance(result.body, ast.Lambda) and len(substring) > len(longest_lambda):
                longest_lambda = substring
    return longest_lambda

def get_lambda_body(f):
    try:
        lambda_str = inspect.getsource(f).strip()
    except OSError as e:
        if str(e) == "could not get source code":
            return "<lambda>"
    return parse_lambda(lambda_str)

def parse_lambda(lambda_str):
    start = lambda_str.find('lambda')
    end = lambda_str.rfind('\n')
    lambda_str = lambda_str[start:end]
    lambdaexpr = longest_lambda_substring(lambda_str)
    match = re.search(r'lambda\s?([a-zA-Z0-9,\s*]*)\s*:(.*)', lambdaexpr)
    if match:
        args, body = match.groups()

        if 'lambda' in body:
            body = parse_lambda(body.strip())
        
        return f"{'λ'+args} -> {body.strip()}"
    else:
        return None
    
def function_to_str(f: callable) -> str:
    function_name = f.__name__
    if function_name == '<lambda>':
        function_name = get_lambda_body(f)
    
    output = f"{function_name}"
    return output

A = TypeVar('A')
B = TypeVar('B')

# Adapted from functools.reduce

class _initial_missing(object): ...

_default_initial = _initial_missing()

def foldl(function):
    def __foldl(sequence: Iterable[A], initial: B=_default_initial) -> B:
        it = iter(sequence)

        if isinstance(initial, _initial_missing):
            try:
                value = next(it)
            except StopIteration:
                raise TypeError(
                    "foldl() of empty iterable with no initial value") from None
        else:
            value = initial

        for element in it:
            value = function(value, element)

        return value
    
    __foldl.__name__ = f'foldl({function_to_str(function)})'
    return __foldl

def foldr(binary_operation: Callable[[A,B], B]):
    def _foldr(sequence: Iterable[A], initial: B=_default_initial) -> B:
        it = iter(sequence)

        if isinstance(initial, _initial_missing):
            try:
                value = next(it)
            except StopIteration:
                raise TypeError(
                    "foldr() of empty iterable with no initial value") from None
        else:
            value = initial

        for element in it:
            value = binary_operation(element, value)

        return value
    
    _foldr.__name__ = f'foldr({function_to_str(binary_operation)})'
    return _foldr

class Action:
    def __init__(self, f: callable):
        self.f = f
    
    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)
    
    def __str__(self, showclass=True):
        output = function_to_str(self.f)
        if showclass:
            output = f"{self.__class__.__name__}({output})"
        return output
    
    def __repr__(self):
        return str(self)

class Then(Action):
    def __init__(self, f: callable):
        super().__init__(f)

class Run(Action):
    def __init__(self, f: callable):
        super().__init__(f)

class Map(Action):
    def __init__(self, *fs: callable):
        self.fs = fs

class Mapply(Action):
    def __init__(self, fs: list):
        self.fs = fs

class Foreach(Action):
    def __init__(self, f: callable):
        self.f = f

class Chain:
    class MissingInput(object): ...
    MISSING_INPUT = MissingInput()

    def __init__(self, input=MISSING_INPUT, functions=None):
        self.input = input
        self.functions = [] if functions is None else functions

    # Start the chain
    @staticmethod
    def do(callable, action=None):
        actions = {
            'bind': Then,
            'run': Run,
        }
        
        if action is None:
            action = 'bind'

        action = actions.get(action)
        
        if action is None:
            raise ValueError(f"Invalid action: {action}. Valid options are: {', '.join(actions.keys())}")
        
        return Chain(functions=[action(callable)])

        #return Chain(functions=[Then(callable)])

    # Monadic bind (>==)
    def then(self, callable):
        return Chain(self.input, self.functions + [Then(callable)])

    # Monadic then (>>)
    def run(self, callable):
        return Chain(self.input, self.functions + [Run(callable)])

    # Insert input into the chain
    def start(self, input):
        return Chain(input, self.functions)
    
    # self.functions <*> [self.input]
    def map(self, *callables):
        return Chain(self.input, self.functions + [Map(*callables)])
    
    # Glue two chains together
    def glue(self, chain):
        return Chain(self.input, self.functions + chain.functions)
    
     # Mapply
    def mapply(self, *callables):
        return Chain(self.input, self.functions + [Mapply(callables)])
    
    # Foreach
    def foreach(self, callable):
        return Chain(self.input, self.functions + [Foreach(callable)])

    # Execute the chain
    def compute(self):
        result = self.input
        for function in self.functions:
            if isinstance(function, Then):
                result = function(result)
            elif isinstance(function, Run):
                function(result)
            elif isinstance(function, Map):
                result = tuple(f(result) for f in function.fs)
            elif isinstance(function, Mapply):
                if len(result) != len(function.fs):
                    raise ValueError(f"Shapes don't match, expected {len(function.fs)} but got {len(result)}.")
                result = tuple(f(x) for f, x in zip(function.fs, result))
            elif isinstance(function, Foreach):
                if not isinstance(result, Iterable):
                    raise ValueError("Input is not iterable")
                result = [function.f(x) for x in result]
        return Chain(result)

    # Unwrap the result
    def result(self, *args, **kwargs):
        return self.input
    
    def __str__(self) -> str:
        input = '<empty>'
        if self.input is not self.MISSING_INPUT:
            input = str(self.input)
        
        functions = []
        for i, function in enumerate(self.functions):
            if isinstance(function, Then):
                operator = ' >== '
            elif isinstance(function, Run):
                operator = ' >> '
            elif isinstance(function, Map):
                functions.append(f" <| [{', '.join(map(lambda x: Action(x).__str__(showclass=False), function.fs))}]")
                continue
            elif isinstance(function, Mapply):
                functions.append(f" || [{', '.join(map(lambda x: Action(x).__str__(showclass=False), function.fs))}]")
                continue
            elif isinstance(function, Foreach):
                operator = ' <$> '
            
            if i == 0:
                operator = ''
            
            function_string = str(function) if isinstance(function, Chain) else function.__str__(showclass=False)
            functions.append(operator+function_string)
        
        functions = ''.join(functions) if len(functions) > 0 else '<empty>'
            
        return f"Chain({input} | {functions})"

    def __repr__(self) -> str:
        return str(self)
    
    def __rshift__(self, other):
        # Overload the >> operator to represent 'then'
        return self.then(other)
    
    def __and__(self, other):
        # Overload the '&' operator to represent 'run'
        return self.run(other)

    def __or__(self, other):
        # Overload the '|' operator to represent 'map'
        return self.map(*other)
    
    def __gt__(self, other):
        # Overload the > operator to represent 'start'
        return self.start(other)
    
    def __lt__(self, other):
        # Overload the < operator to represent 'start'
        return self.start(other)
    