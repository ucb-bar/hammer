#  Helper and utility classes for testing hammer_tech.
#
#  See LICENSE for licence details.

from typing import Optional

import hammer.tech as hammer_tech


class HasGetTech:
    """
    Helper mix-in that adds the convenience function get_tech.
    """

    def get_tech(self, tech_opt: Optional[hammer_tech.HammerTechnology]) -> hammer_tech.HammerTechnology:
        """
        Get the technology from the input parameter or raise an assertion.
        :param tech_opt: Result of HammerTechnology.load_from_dir()
        :return: Technology library or assertion will be raised.
        """
        assert tech_opt is not None, "Technology must be loaded"
        return tech_opt
