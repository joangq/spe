import unittest
from chain import Chain

class TestChain(unittest.TestCase):

    # Chain.do(id).then(f).start(a) ==_obs f(a)
    def test_then_left_identity(self):
        def add_one(x):
            return x + 1

        chain = Chain.do(lambda x: x).then(add_one).start(1).compute().result()
        self.assertEqual(chain, add_one(1))

    # Chain.do(id).then(lambda x: x).start(a) ==_obs Chain.do(id).start(a)
    def test_then_right_identity(self):
        chain = Chain.do(lambda x: x).then(lambda x: x).start(1).compute().result()
        self.assertEqual(chain, 1)

    # Chain.do(id).then(f).then(g).start(a) ==_obs Chain.do(id).then(lambda x: Chain.do(f).then(g).start(x)).start(a)
    def test_then_associativity(self):
        def add_one(x):
            return x + 1

        def multiply_by_two(x):
            return x * 2

        val = 2
        chainx = lambda x: Chain.do(add_one).then(multiply_by_two).start(x).compute().result()
        chain1 = chainx(val)
        chain2 = Chain.do(chainx).start(val).compute().result()
        self.assertEqual(chain1, 6)
        self.assertEqual(chain1, chain2)

    def test_run_left_identity(self):
        def add_one(x):
            return x + 1

        chain = Chain.do(lambda x: x).run(add_one).start(1).compute().result()
        self.assertEqual(chain, 1)

    def test_run_right_identity(self):
        chain = Chain.do(lambda x: x).start(1).run(lambda x: x).compute().result()
        self.assertEqual(chain, 1)

    def test_run_associativity(self):
        def add_one(x):
            return x + 1

        def multiply_by_two(x):
            return x * 2

        val = 2
        chainx = lambda x: Chain.do(add_one).start(x).run(multiply_by_two).compute().result()
        chain1 = chainx(val)
        chain2 = Chain.do(chainx).start(val).compute().result()
        self.assertEqual(chain1, 3)
        self.assertEqual(chain1, chain2)
    
    def test_map(self):
        def add_one(x):
            return x + 1

        def multiply_by_two(x):
            return x * 2

        chain = Chain.do(lambda x: x).map(add_one, multiply_by_two).start(1).compute().result()
        self.assertEqual(chain, (2, 2))

    def test_glue_left_identity(self):
        def add_one(x):
            return x + 1

        chain1 = Chain.do(lambda x: x).glue(Chain.do(add_one)).start(1).compute().result()
        chain2 = Chain.do(add_one).start(1).compute().result()
        self.assertEqual(chain1, chain2)

    def test_glue_right_identity(self):
        chain1 = Chain.do(lambda x: x).glue(Chain.do(lambda x: x)).start(1).compute().result()
        chain2 = Chain.do(lambda x: x).start(1).compute().result()
        self.assertEqual(chain1, chain2)

    def test_glue_associativity(self):
        def add_one(x):
            return x + 1

        def multiply_by_two(x):
            return x * 2

        chain1 = Chain.do(lambda x: x).glue(Chain.do(add_one)).glue(Chain.do(multiply_by_two)).start(1).compute().result()
        chain2 = Chain.do(lambda x: x).glue(Chain.do(lambda x: Chain.do(lambda x: x).glue(Chain.do(add_one)).glue(Chain.do(multiply_by_two)).start(x).compute().result())).start(1).compute().result()
        self.assertEqual(chain1, chain2)
    
    def test_mapply(self):
        def add_one(x):
            return x + 1

        def multiply_by_two(x):
            return x * 2

        chain = Chain.do(lambda x: x).mapply(add_one, multiply_by_two).start([1, 2]).compute().result()
        self.assertEqual(chain, (2, 4))

    def test_mapply_error(self):
        def add_one(x):
            return x + 1

        def multiply_by_two(x):
            return x * 2

        with self.assertRaises(ValueError) as e:
            Chain.do(lambda x: x).mapply(add_one, multiply_by_two).start([1, 2, 3]).compute().result()
    
    def test_foreach(self):
        def add_one(x):
            return x + 1

        chain = Chain.do(lambda x: x).foreach(add_one).start([1, 2, 3]).compute().result()
        self.assertEqual(chain, [2, 3, 4])

    def test_foreach_error(self):
        def add_one(x):
            return x + 1

        with self.assertRaises(ValueError):
            Chain.do(lambda x: x).foreach(add_one).start(1).compute().result()
            