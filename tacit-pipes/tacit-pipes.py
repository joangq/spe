import unittest
from catthy import lista

class staticproperty(property):
    def __get__(self, cls, owner):
        return staticmethod(self.fget).__get__(None, owner)()

class PipeInput:
    missing_init = object()

    def __init__(self, elem):
        if elem == PipeInput.missing_init:
            self.value = None
        else:
            self.value = elem

    @staticmethod
    def create():
        return PipeInput(PipeInput.missing_init)

    def into(self, other: callable):
        return other(self.value)

    def __or__(self, other: callable):
        return self.into(other)

    def __matmul__(self, other):
        self.value = other
        return self

    def __str__(self):
        return f'PipeInput({self.value})'

    def __repr__(self):
        return str(self)

class ParallelComputation:
    fs = lista()

    def __init__(self, *fs):
        self.fs = lista(fs)

    def add_computation(self, other: callable):
        if isinstance(other, ParallelComputation):
            self.fs.extend(other.fs)
        else:
            self.fs.append(other)
        return self

    def __add__(self, other):
        return self.add_computation(other)

    def apply(self, x):
        # noinspection PyTypeChecker
        return tuple(self.fs.apply_to([x]))

    def __call__(self, x):
        return self.apply(x)

    def combine_by(self, other):
        return lambda *args, **kwargs: other(self(*args, **kwargs))

    def __gt__(self, other):
        return self.combine_by(other)


# noinspection PyPep8Naming
# ghci> ((arr (+1)) *** (arr (*2)) *** (arr (/3)) *** (arr (*10))) (1,(2,(3,4)))
#    >> (2,(4,(1.0,40)))
class pipe:
    f: callable

    @staticmethod
    def start(x):
        return PipeInput(x)

    @staticproperty
    def begin():
        return PipeInput.create()

    def __init__(self, f: 'pipe | callable'):
        self.f = f


    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)

    def __add__(self, other: 'pipe'):
        return ParallelComputation(self, other)

    def then(self, f: 'pipe | callable'):
        if not isinstance(f, pipe):
            self.then(pipe(f))

        return pipe( lambda *args, **kwargs: f(self(*args, **kwargs)) )

    def __rshift__(self, f: 'pipe | callable'):
        return self.then(f)

    def after(self, f: 'pipe  | callable'):
        if not isinstance(f, pipe):
            self.after(pipe(f))

        return pipe( lambda *args, **kwargs: self(f(*args, **kwargs)) )

    def __lshift__(self, f: 'pipe | callable'):
        return self.after(f)

    def first(self, t: tuple):
        x, y = t
        return self(x), y

    def second(self, t: tuple):
        x, y = t
        return x, self(y)

    def bifurcate(self, f):  # &&&
        def result(*args, **kwargs):
            return self(*args, **kwargs), f(*args, **kwargs)

        return result

    def bimap(self, f):  # ***
        def result(t):
            x, y = t
            return self(x), f(y)

        return result

def mul_six(x): return 6 * x


def add_ten(x): return 10 + x


def div_two(x): return .5 * x


def sub_one(x): return -1 + x


def read_file(): return 'Hello, World'


def tr(s1, s2):
    return lambda s: s.replace(s1, s2)


def sfind(s1):
    return lambda s: s.find(s1)


class Tests(unittest.TestCase):
    def test_string_manipulation(self):
        input1: str = read_file()
        pipe1: pipe = pipe(tr(' ', '_')).then(sfind('_W'))

        result1 = pipe.start(input1).into(pipe1)
        self.assertEqual(result1, 6)

        input2: str = read_file()
        pipe2: pipe = ...

    def f(self):
        input2 = read_file()
        pipe2 = (pipe(len)
                 .then(pipe(ParallelComputation(add_ten, mul_six)
                            .add_computation(div_two)
                            .add_computation(sub_one)
                            .combine_by(sum))))

        print(
            pipe.start(input2).into(pipe2)
        )


if __name__ == '__main__':
    pipe.begin @ 2 | pipe(lambda x: x + 2) >> str >> len >> (lambda x: x+1) >> mul_six >> print
