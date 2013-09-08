import unittest
from units import Unit

def p(string):
    if '/' in string:
        str_numerator, str_denominator = string.split('/')
        numerator, denominator = str_numerator.split(' '), str_denominator.split(' ')
    else:
        numerator, denominator = string.split(' '), []
    return Unit(numerator, denominator)


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

    def test_normalize(self):
        self.assertEqual(Unit().normalize(), (1, Unit()))
        self.assertEqual(p('m').normalize(), (1, p('meter')))
        self.assertEqual(p('m / m').normalize(), (1, Unit()))
        self.assertEqual(p('m m / m').normalize(), (1, p('meter')))
        self.assertEqual(p('kilometer').normalize(), (1000, p('meter')))
        self.assertEqual(p('meter / kilometer').normalize(), (1 / 1000, Unit()))
        self.assertEqual(p('milligram').normalize(), (1 / 1000, p('gram')))
        self.assertEqual(p('milligram / kilometer').normalize(), (1 / 1000 ** 2, p('gram / meter')))
        self.assertEqual(p('unknown milligram / kilometer').normalize(), (1 / 1000 ** 2, p('unknown gram / meter')))
        self.assertEqual(p('B').normalize(), (8, p('bit')))
        self.assertEqual(p('byte').normalize(), (8, p('bit')))
        self.assertEqual(p('bit').normalize(), (1, p('bit')))
        self.assertEqual(p('unknown').normalize(), (1, p('unknown')))



if __name__ == '__main__':
    unittest.main()


