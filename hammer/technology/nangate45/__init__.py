# OpenROAD-flow's nangate45 plugin for Hammer.
#
# See LICENSE for licence details.

from hammer.tech import HammerTechnology

class Nangate45Tech(HammerTechnology):
    """
    Override the HammerTechnology used in `hammer_tech.py`
    This class is loaded by function `load_from_json`, and will pass 
    the `try` in `importlib`.
    """

tech = Nangate45Tech()
