#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  filters.py
#  A collection of pre-implemented LibraryFilters.
#
#  See LICENSE for licence details.

import os
import warnings
from typing import TYPE_CHECKING, Any, Callable, List

from library_filter import LibraryFilter

if TYPE_CHECKING:
    # grumble grumble, we need a better Library class generator
    from library_filter import Library


class LibraryFilterHolder:
    """
    Dummy class to hold the list of properties.
    Instantiated by hammer_tech to be exposed as hammer_tech.filters.lef_filter etc.
    """

    @staticmethod
    def create_nonempty_check(description: str) -> Callable[[List[str]], List[str]]:
        """
        Create a function that checks that the list it is given has >1 element.
        :param description: Description to show in the error message.
        :return: Function that takes in the list of elements and returns a checked/processed version of itself.
        """
        def check_nonempty(l: List[str]) -> List[str]:
            if len(l) == 0:
                raise ValueError("Must have at least one " + description)
            else:
                return l

        return check_nonempty

    @property
    def timing_db_filter(self) -> LibraryFilter:
        """
        Selecting Synopsys timing libraries (.db). Prefers CCS if available; picks NLDM as a fallback.
        """

        def paths_func(lib: "Library") -> List[str]:
            # Choose ccs if available, if not, nldm.
            if lib.ccs_library_file is not None:
                return [lib.ccs_library_file]
            elif lib.nldm_library_file is not None:
                return [lib.nldm_library_file]
            else:
                return []

        return LibraryFilter.new("timing_db", "CCS/NLDM timing lib (Synopsys .db)", paths_func=paths_func,
                                 is_file=True)

    @property
    def liberty_lib_filter(self) -> LibraryFilter:
        """
        Select ASCII liberty (.lib) timing libraries. Prefers CCS if available; picks NLDM as a fallback.
        """
        warnings.warn("Use timing_lib_filter instead", DeprecationWarning, stacklevel=2)

        def paths_func(lib: "Library") -> List[str]:
            # Choose ccs if available, if not, nldm.
            if lib.ccs_liberty_file is not None:
                return [lib.ccs_liberty_file]
            elif lib.nldm_liberty_file is not None:
                return [lib.nldm_liberty_file]
            else:
                return []

        return LibraryFilter.new("timing_lib", "CCS/NLDM timing lib (ASCII .lib)",
                                 paths_func=paths_func, is_file=True)

    @property
    def timing_lib_filter(self) -> LibraryFilter:
        """
        Select ASCII .lib timing libraries. Prefers CCS if available; picks NLDM as a fallback.
        """

        def paths_func(lib: "Library") -> List[str]:
            # Choose ccs if available, if not, nldm.
            if lib.ccs_liberty_file is not None:
                return [lib.ccs_liberty_file]
            elif lib.nldm_liberty_file is not None:
                return [lib.nldm_liberty_file]
            else:
                return []

        return LibraryFilter.new("timing_lib", "CCS/NLDM timing lib (ASCII .lib)",
                                 paths_func=paths_func, is_file=True)

    @property
    def timing_lib_with_ecsm_filter(self) -> LibraryFilter:
        """
        Select ASCII .lib timing libraries. Prefers ECSM, then CCS, then NLDM if multiple are present for
        a single given .lib.
        """

        def paths_func(lib: "Library") -> List[str]:
            if lib.ecsm_liberty_file is not None:
                return [lib.ecsm_liberty_file]
            elif lib.ccs_liberty_file is not None:
                return [lib.ccs_liberty_file]
            elif lib.nldm_liberty_file is not None:
                return [lib.nldm_liberty_file]
            else:
                return []

        return LibraryFilter.new("timing_lib_with_ecsm", "ECSM/CCS/NLDM timing lib (liberty ASCII .lib)",
                                 paths_func=paths_func, is_file=True)

    @property
    def qrc_tech_filter(self) -> LibraryFilter:
        """
        Selecting qrc RC Corner tech (qrcTech) files.
        """

        def paths_func(lib: "Library") -> List[str]:
            if lib.qrc_techfile is not None:
                return [lib.qrc_techfile]
            else:
                return []

        return LibraryFilter.new("qrc", "qrc RC corner tech file",
                                 paths_func=paths_func, is_file=True)

    @property
    def verilog_synth_filter(self) -> LibraryFilter:
        """
        Selecting verilog_synth files which are synthesizable wrappers (e.g. for SRAM) which are needed in some
        technologies.
        """

        def paths_func(lib: "Library") -> List[str]:
            if lib.verilog_synth is not None:
                return [lib.verilog_synth]
            else:
                return []

        return LibraryFilter.new("verilog_synth", "Synthesizable Verilog wrappers",
                                 paths_func=paths_func, is_file=True)

    @property
    def lef_filter(self) -> LibraryFilter:
        """
        Select LEF files for physical layout.
        """

        def filter_func(lib: "Library") -> bool:
            return lib.lef_file is not None

        def paths_func(lib: "Library") -> List[str]:
            assert lib.lef_file is not None
            return [lib.lef_file]

        def sort_func(lib: "Library"):
            if lib.provides is not None:
                for provided in lib.provides:
                    if provided.lib_type is not None and provided.lib_type == "technology":
                        return 0  # put the technology LEF in front
            return 100  # put it behind

        return LibraryFilter.new("lef", "LEF physical design layout library", is_file=True, filter_func=filter_func,
                                 paths_func=paths_func, sort_func=sort_func)

    @property
    def verilog_sim_filter(self) -> LibraryFilter:
        """
        Select verilog sim files for gate level simulation
        """

        def filter_func(lib: "Library") -> bool:
            return lib.verilog_sim is not None

        def paths_func(lib: "Library") -> List[str]:
            assert lib.verilog_sim is not None
            return [lib.verilog_sim]

        return LibraryFilter.new("verilog_sim", "Gate-level verilog sources", is_file=True, filter_func=filter_func, paths_func=paths_func)

    @property
    def gds_filter(self) -> LibraryFilter:
        """
        Select GDS files for opaque physical information.
        """

        def filter_func(lib: "Library") -> bool:
            return lib.gds_file is not None

        def paths_func(lib: "Library") -> List[str]:
            assert lib.gds_file is not None
            return [lib.gds_file]

        return LibraryFilter.new("gds", "GDS opaque physical design layout", is_file=True, filter_func=filter_func,
                                 paths_func=paths_func)

    @property
    def spice_filter(self) -> LibraryFilter:
        """
        Select SPICE files.
        """

        def filter_func(lib: "Library") -> bool:
            return lib.spice_file is not None

        def paths_func(lib: "Library") -> List[str]:
            assert lib.spice_file is not None
            return [lib.spice_file]

        return LibraryFilter.new("spice", "SPICE files", is_file=True, filter_func=filter_func,
                                 paths_func=paths_func)

    @property
    def milkyway_lib_dir_filter(self) -> LibraryFilter:
        def select_milkyway_lib(lib: "Library") -> List[str]:
            if lib.milkyway_lib_in_dir is not None:
                return [os.path.dirname(lib.milkyway_lib_in_dir)]
            else:
                return []

        return LibraryFilter.new("milkyway_dir", "Milkyway lib", is_file=False, paths_func=select_milkyway_lib)

    @property
    def milkyway_techfile_filter(self) -> LibraryFilter:
        """Select milkyway techfiles."""

        def select_milkyway_tfs(lib: "Library") -> List[str]:
            if lib.milkyway_techfile is not None:
                return [lib.milkyway_techfile]
            else:
                return []

        return LibraryFilter.new("milkyway_tf", "Milkyway techfile", is_file=True, paths_func=select_milkyway_tfs,
                                 extra_post_filter_funcs=[self.create_nonempty_check("Milkyway techfile")])

    @property
    def tlu_max_cap_filter(self) -> LibraryFilter:
        """Select TLU+ max cap files."""

        def select_tlu_max_cap(lib: "Library") -> List[str]:
            if lib.tluplus_files is not None and lib.tluplus_files.max_cap is not None:
                return [lib.tluplus_files.max_cap]
            else:
                return []

        return LibraryFilter.new("tlu_max", "TLU+ max cap db", is_file=True, paths_func=select_tlu_max_cap)

    @property
    def tlu_min_cap_filter(self) -> LibraryFilter:
        """Select TLU+ min cap files."""

        def select_tlu_min_cap(lib: "Library") -> List[str]:
            if lib.tluplus_files is not None and lib.tluplus_files.min_cap is not None:
                return [lib.tluplus_files.min_cap]
            else:
                return []

        return LibraryFilter.new("tlu_min", "TLU+ min cap db", is_file=True, paths_func=select_tlu_min_cap)

    @property
    def tlu_map_file_filter(self) -> LibraryFilter:
        """Select TLU+ map files."""
        def select_tlu_map_file(lib: "Library") -> List[str]:
            if lib.tluplus_map_file is not None:
                return [lib.tluplus_map_file]
            else:
                return []
        return LibraryFilter.new("tlu_map", "TLU+ map file", is_file=True, paths_func=select_tlu_map_file)

    @property
    def spice_model_file_filter(self) -> LibraryFilter:
        """Select spice model files."""
        def select_spice_model_file(lib: "Library") -> List[str]:
            if lib.spice_model_file is not None and lib.spice_model_file.path is not None:
                return [lib.spice_model_file.path]
            else:
                return []
        return LibraryFilter.new("spice_model_file", "Spice model file", is_file=True, paths_func=select_spice_model_file)

    @property
    def spice_model_lib_corner_filter(self) -> LibraryFilter:
        """Select spice model lib corners."""
        def select_spice_model_lib_corner(lib: "Library") -> List[str]:
            if lib.spice_model_file is not None and lib.spice_model_file.lib_corner is not None:
                return [lib.spice_model_file.lib_corner]
            else:
                return []
        return LibraryFilter.new("spice_model_lib_corner", "Spice model lib corner", is_file=False, paths_func=select_spice_model_lib_corner)

    @property
    def power_grid_library_filter(self) -> LibraryFilter:
        """
        Select power grid libraries for EM/IR analysis.
        """

        def filter_func(lib: "Library") -> bool:
            return lib.power_grid_library is not None

        def paths_func(lib: "Library") -> List[str]:
            assert lib.power_grid_library is not None
            return [lib.power_grid_library]

        def sort_func(lib: "Library"):
            if lib.provides is not None:
                for provided in lib.provides:
                    if provided.lib_type is not None and provided.lib_type == "technology":
                        return 0  # put the technology library in front
            return 100  # put it behind

        return LibraryFilter.new("power_grid_library", "Power grid library", is_file=False, filter_func=filter_func,
                                 paths_func=paths_func, sort_func=sort_func)

    @property
    def klayout_techfile_filter(self) -> LibraryFilter:
        """
        Select KLayout tech files for GDS streaming.
        """

        def filter_func(lib: "Library") -> bool:
            return lib.klayout_techfile is not None

        def paths_func(lib: "Library") -> List[str]:
            assert lib.klayout_techfile is not None
            return [lib.klayout_techfile]

        return LibraryFilter.new("klayout", "GDS streaming", is_file=True, filter_func=filter_func, 
                                 paths_func=paths_func)
