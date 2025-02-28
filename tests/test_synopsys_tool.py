import unittest
import sys
import os

# Add the hammer path to the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hammer.common.synopsys import SynopsysTool

class TestSynopsysTool(unittest.TestCase):
    """Test the SynopsysTool class"""
    
    def setUp(self):
        # Create an instance of SynopsysTool for testing
        class MinimalSynopsysTool(SynopsysTool):
            def tool_config_prefix(self):
                return "synopsys"
            
            def get_setting(self, key, default=None):
                return default
                
            # Implement the abstract method steps
            def steps(self):
                return []
        
        self.tool = MinimalSynopsysTool()
    
    def test_version_number_icv_formats(self):
        """Test actual ICV version formats."""
        # Test S-2021.06-SP3-2 format
        version1 = "S-2021.06-SP3-2"
        expected1 = (2021 * 100 + 6) * 100 + 3  # The method should extract 3 from SP3-2
        self.assertEqual(self.tool.version_number(version1), expected1)
        
        # Test W-2024.09-4 format
        version2 = "W-2024.09-4"
        expected2 = (2024 * 100 + 9) * 100 + 4
        self.assertEqual(self.tool.version_number(version2), expected2)
        
        # Test V-2023.09-SP2 format
        version3 = "V-2023.09-SP2"
        expected3 = (2023 * 100 + 9) * 100 + 2
        self.assertEqual(self.tool.version_number(version3), expected3)


if __name__ == '__main__':
    unittest.main()