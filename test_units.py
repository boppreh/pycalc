import unittest
from units import Unit

class TestUnit(unittest.TestCase):
    def test_creation(self):
        u = Unit()
        self.assertFalse(u)
        self.assertEquals(u.numerator, [])
        self.assertEquals(u.denominator, [])

        u = Unit(('a',))
        self.assertTrue(u)
        self.assertEquals(u.numerator, ['a'])
        self.assertEquals(u.denominator, [])

        u = Unit((), ('a',))
        self.assertTrue(u)
        self.assertEquals(u.numerator, [])
        self.assertEquals(u.denominator, ['a'])

if __name__ == '__main__':
    unittest.main()

