import unittest
from gdsii import library, elements
import os.path

class TestLibraryLoad(unittest.TestCase):
    def setUp(self):
        file_name = os.path.join(os.path.dirname(__file__), 'data', 'test1.gds')
        with open(file_name, 'rb') as stream:
            self.library = library.Library.load(stream)

    def test_library(self):
        library = self.library
        self.assertEqual(library.version, 5)
        self.assertEqual(library.name, b'TEST.DB')
        self.assertEqual(library.mod_time.isoformat(), '2010-08-17T14:22:22')
        self.assertEqual(library.acc_time.isoformat(), '2010-08-17T14:36:21')
        self.assertAlmostEqual(library.physical_unit, 1e-9)
        self.assertAlmostEqual(library.logical_unit, 0.001)

    def test_structure(self):
        library = self.library
        self.assertEqual(len(library), 1)
        struc = library[0]
        self.assertEqual(struc.name, b'test_struc1')
        self.assertEqual(struc.mod_time.isoformat(), '1970-01-01T01:00:00')
        self.assertEqual(struc.acc_time.isoformat(), '2010-08-17T14:35:55')
        self.assertEqual(struc.strclass, None)

    def test_elements(self):
        struc = self.library[0]
        self.assertEqual(len(struc), 2)
        elem = struc[0]
        self.assertTrue(isinstance(elem, elements.Boundary))
        self.assertEqual(elem.layer, 34)
        self.assertEqual(elem.data_type, 0)
        self.assertEqual(elem.xy, [(33100, -198900), (48100, -198900), (48100, -186800),
            (33100, -186800), (33100, -198900)])
        self.assertEqual(elem.properties, []) # TODO it should not be so
        elem = struc[1]
        self.assertTrue(isinstance(elem, elements.Path))
        self.assertEqual(elem.layer, 44)
        self.assertEqual(elem.data_type, 0)
        self.assertEqual(elem.path_type, 0)
        self.assertEqual(elem.width, 15000)
        self.assertEqual(elem.xy, [(-125000, 0), (-125000, -52000), (-52000, -125000), (13100, -125000)])
        self.assertEqual(len(elem.properties), 2)
        self.assertEqual(elem.properties[0], (1, b'test property 1'))
        self.assertEqual(elem.properties[1], (2, b'test property 2'))

test_cases = (TestLibraryLoad,)

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

if __name__ == '__main__':
    unittest.main()
