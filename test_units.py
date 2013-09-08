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
        self.assertEqual(self.empty.numerator, [])
        self.assertEqual(self.empty.denominator, [])

        self.assertTrue(self.num)
        self.assertEqual(self.num.numerator, ['a'])
        self.assertEqual(self.num.denominator, [])

        self.assertTrue(self.den)
        self.assertEqual(self.den.numerator, [])
        self.assertEqual(self.den.denominator, ['b'])

        self.assertTrue(self.multiple)
        self.assertEqual(self.multiple.numerator, ['a', 'a', 'c'])
        self.assertEqual(self.multiple.denominator, ['b', 'd'])

    def test_mul(self):
        self.assertEqual(self.multiple * self.full, self.full * self.multiple)
        self.assertEqual(self.empty * self.num, self.num)
        self.assertEqual(self.empty * self.den, self.den)
        self.assertEqual(self.num * self.den, self.full)

    def test_str(self):
        self.assertEqual(str(self.empty), '')
        self.assertEqual(str(self.num), 'a')
        self.assertEqual(str(self.den), ' / b')
        self.assertEqual(str(self.multiple), 'a^2 c / b d')



if __name__ == '__main__':
    unittest.main()


