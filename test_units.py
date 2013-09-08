import unittest
from units import Unit

class TestUnit(unittest.TestCase):
    def setUp(self):
        self.empty = Unit()
        self.num = Unit(('a',), ())
        self.den = Unit((), ('b',))
        self.full = Unit(('a',), ('b',))
        self.multiple = Unit(('a', 'a', 'c'), ('b', 'd'))

    def test_creation(self):
        self.assertFalse(self.empty)
        self.assertEquals(self.empty.numerator, [])
        self.assertEquals(self.empty.denominator, [])

        self.assertTrue(self.num)
        self.assertEquals(self.num.numerator, ['a'])
        self.assertEquals(self.num.denominator, [])

        self.assertTrue(self.den)
        self.assertEquals(self.den.numerator, [])
        self.assertEquals(self.den.denominator, ['b'])

        self.assertTrue(self.multiple)
        self.assertEquals(self.multiple.numerator, ['a', 'a', 'c'])
        self.assertEquals(self.multiple.denominator, ['b', 'd'])

    def test_mul(self):
        self.assertEquals(self.multiple * self.full, self.full * self.multiple)
        self.assertEquals(self.empty * self.num, self.num)
        self.assertEquals(self.empty * self.den, self.den)
        self.assertEquals(self.num * self.den, self.full)



if __name__ == '__main__':
    unittest.main()

