import unittest
from gdsii.record import _parse_real8, _pack_real8, _int_to_real, _real_to_int
from gdsii import exceptions
import struct

class TestReal8(unittest.TestCase):
    data = {
        0x4110000000000000: 1.0,
        0x4120000000000000: 2.0,
        0x4130000000000000: 3.0,
        0xC110000000000000: -1.0,
        0xC120000000000000: -2.0,
        0xC130000000000000: -3.0,
        0x4080000000000000: 0.5,
        0x4099999999999999: 0.6,
        0x40B3333333333333: 0.7,
        0x4118000000000000: 1.5,
        0x4119999999999999: 1.6,
        0x411B333333333333: 1.7,
        0x0000000000000000: 0.0,
        0x41A0000000000000: 10.0,
        0x4264000000000000: 100.0,
        0x433E800000000000: 1000.0, # there is error in doc?
        0x4427100000000000: 10000.0,
        0x45186A0000000000: 100000.0
    }

    def test_from_int(self):
        for int_val, real_val in self.data.items():
            self.assertAlmostEqual(_int_to_real(int_val),  real_val)

    def test_to_int(self):
        for int_val, real_val in self.data.items():
            self.assertAlmostEqual(real_val, _int_to_real(_real_to_int(real_val)))

    def test_parse(self):
        packed_data = struct.pack('>{0}Q'.format(len(self.data)), *self.data.keys())
        unpacked = _parse_real8(packed_data)
        expected_results = list(self.data.values())
        self.assertEqual(len(unpacked), len(expected_results))
        for i in range(len(unpacked)):
            self.assertAlmostEqual(unpacked[i], expected_results[i])

    def test_pack(self):
        packed_data = _pack_real8(self.data.values())
        unpacked = _parse_real8(packed_data)
        expected_results = list(self.data.values())
        self.assertEqual(len(unpacked), len(expected_results))
        for i in range(len(unpacked)):
            self.assertAlmostEqual(unpacked[i], expected_results[i])

    def test_exceptions(self):
        for i in range(8):
            self.assertRaises(exceptions.IncorrectDataSize, _parse_real8, b' '*i)

test_cases = (TestReal8,)

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

if __name__ == '__main__':
    unittest.main()
