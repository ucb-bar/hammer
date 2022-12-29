#  hammer-vlsi plugin for generic PCB deliverables. This can generate
#  footprints, schematic symbols, and CSVs for visualizing the bump map.
#
#  See LICENSE for licence details.

import os
import datetime
import re
from typing import List, Dict, Tuple
from decimal import Decimal
from hammer.utils import um2mm

from hammer.vlsi import HammerPCBDeliverableTool, HammerToolStep, BumpsPinNamingScheme, BumpsDefinition, BumpAssignment

class GenericPCBDeliverableTool(HammerPCBDeliverableTool):

    def tool_config_prefix(self) -> str:
        return "pcb.generic"

    def version_number(self, version: str) -> int:
        return 1

    def fill_outputs(self) -> bool:
        self.output_footprints = [self.output_footprint_filename]
        self.output_schematic_symbols = [self.output_schematic_symbol_filename]
        return True

    @property
    def steps(self) -> List[HammerToolStep]:
        steps = [
            self.create_footprint_csv,
            self.create_footprint,
            self.create_bom_builder_pindata_txt,
            self.create_schematic_symbols
        ]
        return self.make_steps_from_methods(steps)

    @property
    def output_footprint_filename(self) -> str:
        # change this when supporting other types
        return os.path.join(self.run_dir, "{top}-pads.d".format(top=self.top_module))

    @property
    def output_footprint_csv_filename(self) -> str:
        return os.path.join(self.run_dir, "{top}-pads.csv".format(top=self.top_module))

    @property
    def output_schematic_symbol_filename(self) -> str:
        # change this when supporting other types
        return os.path.join(self.run_dir, "{top}-symbol.csv".format(top=self.top_module))

    @property
    def output_bom_builder_pindata_filename(self) -> str:
        return os.path.join(self.run_dir, "{top}-pindata.txt".format(top=self.top_module))

    @property
    def footprint_name(self) -> str:
        return "TESTCHIP-{}".format(self.top_module)

    @property
    def bump_pad_opening_diameter(self) -> Decimal:
        """
        Get the diameter of the PCB footprint pad opening in post-shrink um.
        """
        diameter = self.get_setting("technology.pcb.bump_pad_opening_diameter")
        if diameter is None:
            raise ValueError("Must provide a technology.pcb.bump_pad_opening_diameter if generating PCB deliverables.")
        else:
            return Decimal(str(diameter))

    @property
    def bump_pad_metal_diameter(self) -> Decimal:
        """
        Get the diameter of the PCB footprint pad metal in post-shrink um.
        """
        diameter = self.get_setting("technology.pcb.bump_pad_metal_diameter")
        if diameter is None:
            raise ValueError("Must provide a technology.pcb.bump_pad_metal_diameter if generating PCB deliverables.")
        else:
            return Decimal(str(diameter))

    def get_bumps_and_assignments(self) -> Tuple[BumpsDefinition, List[BumpAssignment]]:
        """
        Helper method to get non-Optional versions of the bumps definition and bumps assignment list.
        """
        bumps = self.get_bumps()
        if bumps is None:
            raise ValueError("There must be a bumps definition in order to generate to generate PCB deliverables!")
        assert isinstance(bumps, BumpsDefinition)

        assignments = bumps.assignments
        if assignments is None:
            raise ValueError("There must be at least 1 bump in order to generate PCB deliverables!")
        assert isinstance(assignments, list)

        if bumps.x < 1 or bumps.y < 1 or len(bumps.assignments) < 1:
            raise ValueError("There must be at least 1 bump in order to generate PCB deliverables!")

        return (bumps, assignments)

    def create_bom_builder_pindata_txt(self) -> bool:
        """
        Creates a PINDATA.txt file that is consumed by the BOMBuilder tool to create a package.
        BOMBuilder is part of the PartSync tool suite: http://www.partsync.com/
        """

        bumps, assignments = self.get_bumps_and_assignments()
        naming_scheme = self.naming_scheme

        # Sort the bumps
        sorted_assignments = naming_scheme.sort_by_name(bumps, assignments)

        # Use post-shrink pitch
        pitch = self.technology.get_post_shrink_length(bumps.pitch)

        # There is no meaningful verion for this file
        # Set the units to metric (mm)
        output = "VER 0.0\nUNIT M\n"
        x_offset = ((1 - bumps.x) * pitch) / 2  # type: Decimal
        y_offset = ((1 - bumps.y) * pitch) / 2  # type: Decimal
        for bump in sorted_assignments:
            # note that the flip-chip mirroring happens here
            name = naming_scheme.name_bump(bumps, bump)
            x = um2mm(Decimal(str(bumps.x - bump.x)) * pitch + x_offset, 3)
            y = um2mm(Decimal(str(bump.y - 1)) * pitch + y_offset, 3)
            # Fields in order (with valid options):
            # Name
            # X position (mm)
            # Y position (mm)
            # Shape (RND or RECT)
            # Width (mm)
            # Height (mm)
            # Side (TOP or BOT)
            # Connection offset X (mm)
            # Connection offset Y (mm)
            # Lead type (0 = signal pin, 1 = mounting hole, 2 = shield)
            # Hole lock (T = true, F = false)
            # Plated/Not Plated (P = Plated, N = Not plated)
            output += "{name:<6} {x:>10.3f} {y:>10.3f} RND {w:0.3f} {w:0.3f} NONE SMT TOP 0 0 0 F P\n".format(name=name, x=x, y=y, w=um2mm(self.bump_pad_metal_diameter, 3))

        with open(self.output_bom_builder_pindata_filename, "w") as f:
            f.write(output)

        return True

    def create_footprint_csv(self) -> bool:
        """
        Create a CSV of the bump map to be easily read into your spreadsheet editor of choice.
        This will fail silently with non-integer bump assignment coordinates (they'll be ignored).

        :return: True if successful
        """

        bumps, assignments = self.get_bumps_and_assignments()

        output = ""
        for y in range(bumps.y,0,-1):
            for x in range(1,bumps.x+1):
                # This is a pretty inefficient algorithm for this task
                matches = [z for z in bumps.assignments if z.x == x and z.y == y]
                if len(matches) > 0:
                    output += str(matches[0].name)
                output += ","
            output += "\n"

        with open(self.output_footprint_csv_filename, "w") as f:
            f.write(output)

        return True

    def create_footprint(self) -> bool:
        """
        Create the footprint type requested by pcb.generic.footprint_type. Currently only supports PADS-V9,
        and does not correctly output soldermask or solderpaste openings.

        :return: True if successful
        """
        footprint_type = str(self.get_setting("pcb.generic.footprint_type"))
        if footprint_type != "PADS-V9":
            raise NotImplementedError("Unsupported footprint type: {}".format(footprint_type))

        bumps, assignments = self.get_bumps_and_assignments()

        # Use post-shrink pitch
        pitch = self.technology.get_post_shrink_length(bumps.pitch)

        # Here is a good ref for the PADS V9 format:
        # ftp://ftp.freecalypso.org/pub/CAD/PADS/pdfdocs/Plib_ASCII.pdf

        # for now, let's make the outline 4 pitches larger than the bump array
        outline_width = ((bumps.x + 3) * pitch)
        outline_height = ((bumps.y + 3) * pitch)

        output = "*PADS-LIBRARY-PCB-DECALS-V9*\n\n"
        # Fields in order from left to right
        # name
        # coordinate units type (M=metric, mm)
        # origin x
        # origin y
        # number of attributes (0)
        # number of labels (0)
        # number of drawing pieces (1: the outline)
        # number of free text strings (0)
        # number of terminals (number of bumps)
        # number of pad stack definitions (1)
        # maxlayers mode (0 = standard)
        output += "{top} M 0 0 0 0 1 0 {terminals} 1 0\n".format(top=self.footprint_name, terminals=len(bumps.assignments))

        # create the timestamp
        output += datetime.datetime.now().strftime("TIMESTAMP %Y.%m.%d.%H.%M.%S\n")

        # create the outline
        # 6 points, 0.1 mm wide, layer 1, solid line
        output += "OPEN 6 0.1 1 -1\n"

        # we'll dog-ear the outline to indicate the reference bump in the top left
        # x and y are in mm, not um
        output += "{x} {y}\n".format(x=um2mm(-outline_width/2, 3),           y=um2mm(-outline_height/2, 3))
        output += "{x} {y}\n".format(x=um2mm(-outline_width/2, 3),           y=um2mm( outline_height/2 - 2*pitch, 3))
        output += "{x} {y}\n".format(x=um2mm(-outline_width/2 + 2*pitch, 3), y=um2mm( outline_height/2, 3))
        output += "{x} {y}\n".format(x=um2mm( outline_width/2, 3),           y=um2mm( outline_height/2, 3))
        output += "{x} {y}\n".format(x=um2mm( outline_width/2, 3),           y=um2mm(-outline_height/2, 3))
        output += "{x} {y}\n".format(x=um2mm(-outline_width/2, 3),           y=um2mm(-outline_height/2, 3))

        # create all of the terminals
        x_offset = ((1 - bumps.x) * pitch) / 2  # type: Decimal
        y_offset = ((1 - bumps.y) * pitch) / 2  # type: Decimal
        naming_scheme = self.naming_scheme
        for bump in bumps.assignments:
            # note that the flip-chip mirroring happens here
            x = um2mm(Decimal(str(bumps.x - bump.x)) * pitch + x_offset, 3)
            y = um2mm(Decimal(str(bump.y - 1)) * pitch + y_offset, 3)
            label = naming_scheme.name_bump(bumps, bump)
            output += "T{x} {y} {x} {y} {label}\n".format(x=x, y=y, label=label)

        # create the pad definition
        # 0=default pad
        # 3=num layer lines
        # P=plated
        # 0=drill diameter (0=no drill)
        output += "PAD 0 3 P 0\n"
        # -2=top layer
        # diameter
        # R=round pad
        output += "-2 {dia} R\n".format(dia=um2mm(self.bump_pad_opening_diameter, 3))
        # -1=all inner layers
        # 0=no pad
        # R=round pad
        output += "-1 0 R\n"
        # 0=bottom layer
        # 0=no pad
        # R=round pad
        output += "0 0 R\n"

        output += "\n*END*"

        with open(self.output_footprint_filename, "w") as f:
            f.write(output)

        return True

    def create_schematic_symbols(self) -> bool:
        """
        Create the schematic symbol type requested by pcb.generic.schematic_symbol_type. Currently only supports
        AltiumCSV, which is a format Altium allows to be copy-and-pasted into the schematic symbol wizard.
        This will divide the pins into groups based on their "group" field.

        :return: True if successful
        """
        schematic_symbol_type = str(self.get_setting("pcb.generic.schematic_symbol_type"))
        if schematic_symbol_type != "AltiumCSV":
            raise NotImplementedError("Unsupported schematic symbool type: {}".format(schematic_symbol_type))

        bumps, assignments = self.get_bumps_and_assignments()

        naming_scheme = self.naming_scheme
        groups = {}  # type: Dict[str, List[BumpAssignment]]

        for a in assignments:
            group = a.group
            if a.group is None:
                # TODO make me smarter
                if a.name in ["VDD", "VSS"]:
                    group = a.name
                else:
                    group = "ungrouped"
            assert isinstance(group, str)


            if group not in groups:
                groups[group] = [a]
            else:
                # Cap each group at 50
                while group in groups and len(groups[group]) >= 50:
                    match = re.match(r"^(.*)_(\d+)$", group)
                    if match:
                        old = int(match.group(2))
                        group = match.group(1) + "_{new}".format(new=old+1)
                    else:
                        group = group + "_1"

                if group not in groups:
                    groups[group] = [a]
                else:
                    groups[group].append(a)

        group_names = sorted([n for n in groups])
        num_rows = max([len(v) for k,v in groups.items()])

        output = ""
        # Build the headers
        for group in group_names:
            output += "{group},,,,,,,,".format(group=group)
        output += "\n"
        # Now the column headers
        for group in group_names:
            output += "Position,Group,Display Name,Designator,Electrical Type,Description,Side,,"
        output += "\n"

        for i in range(num_rows):
            for group in group_names:
                if len(groups[group]) > i:
                    bump = groups[group][i]
                    # TODO(johnwright) Use the Verilog to make Passive actually have a meaningful direction
                    output += "{pos},,{name},{des},Passive,,Left,,".format(pos=i+1,name=bump.name,des=naming_scheme.name_bump(bumps, bump))
                else:
                    output += ",,,,,,,,"
            output += "\n"

        with open(self.output_schematic_symbol_filename, "w") as f:
            f.write(output)


        return True


tool = GenericPCBDeliverableTool
