#  hammer_build_systems.py
#  Class containing all the methods to create VLSI flow build system infrastructure
#
#  See LICENSE for licence details.

from .driver import HammerDriver

import os
import sys
import textwrap
from typing import List, Dict, Tuple, Callable, Optional
from abc import abstractmethod
from .hammer_vlsi_impl import HierarchicalMode
from hammer.utils import get_or_else

class MakeRecipe:
    @abstractmethod
    def phony_target(self) -> str:
        pass

    @abstractmethod
    def recipe(self) -> str:
        pass

    @abstractmethod
    def redo_recipe(self) -> str:
        pass

class MakeActionRecipe(MakeRecipe):
    def __init__(self,
        # Name of the action
        action: str,
        # Override input configuration files
        proj_confs: Optional[str] = None,
        # Override the recipe dependencies
        deps_ovrd: Optional[str] = None,
        # Hierarchical target
        hier: bool = True
    ):
        self.action = action
        self.base = action.split("-")[0]
        rd_suffix = "{suffix}" if hier else "-rundir"
        self.rundir = os.path.join("{obj_dir}", f"{action}{rd_suffix}")
        self.out_file = os.path.join(self.rundir, f"{self.base}-output-full.json")
        default_pconf = [os.path.join("{obj_dir}", f"{action}-input.json")]
        if self.base == "power":  # power inputs are different
            lvl = action.split("-")[-1]
            if lvl == "rtl":
                default_pconf = [os.path.join("{obj_dir}", f"power-sim-{lvl}-input.json")]
            else:
                default_pconf.append(os.path.join("{obj_dir}", f"power-sim-{lvl}-input.json"))
        self.pconf_str = get_or_else(proj_confs, "-p " + " -p ".join(default_pconf))
        self.deps = get_or_else(deps_ovrd, " ".join(default_pconf))

    def phony_target(self) -> str:
        return f"{self.action}{{suffix}}: {self.out_file}"

    def recipe(self) -> str:
        return textwrap.dedent(f"""
            {self.out_file}: {self.deps} $(HAMMER_{self.action.upper()}_DEPENDENCIES)
            \t$(HAMMER_EXEC) {{env_confs}} {self.pconf_str} $(HAMMER_EXTRA_ARGS) --{self.base}_rundir {self.rundir} --obj_dir {{obj_dir}} {self.base}{{suffix}}
            """)

    def redo_recipe(self) -> str:
        return textwrap.dedent(f"""
            redo-{self.action}{{suffix}}:
            \t$(HAMMER_EXEC) {{env_confs}} {self.pconf_str} $(HAMMER_EXTRA_ARGS) --{self.base}_rundir {self.rundir} --obj_dir {{obj_dir}} {self.base}{{suffix}}
            """)

class MakeLinkRecipe(MakeRecipe):
    def __init__(self,
        # Name of the action
        action: str,
        # Hierarchical target
        hier: bool = True
    ):
        self.action = action
        (x, y) = action.split("-to-")
        x_base = x.split("-")[0]
        self.base = x_base + "-to-" + y
        rd_suffix = "{suffix}" if hier else "-rundir"
        self.x_out = os.path.join("{obj_dir}", f"{x}{rd_suffix}", f"{x_base}-output-full.json")
        # Actions that can happen after multiple actions (rtl, syn, par)
        if y in ["sim", "power", "formal", "timing"]:
            y += "-" + x
        y_in_suffix = "{suffix}-input" if hier else "-input"
        self.y_in = os.path.join("{obj_dir}", f"{y}{y_in_suffix}.json")

    def phony_target(self) -> str:
        return f"{self.action}{{suffix}}: {self.y_in}"

    def recipe(self) -> str:
        return textwrap.dedent(f"""
            {self.y_in}: {self.x_out}
            \t$(HAMMER_EXEC) {{env_confs}} -p {self.x_out} $(HAMMER_EXTRA_ARGS) -o {self.y_in} --obj_dir {{obj_dir}} {self.base}
            """)

    def redo_recipe(self) -> str:
        return textwrap.dedent(f"""
            redo-{self.action}{{suffix}}:
            \t$(HAMMER_EXEC) {{env_confs}} -p {self.x_out} $(HAMMER_EXTRA_ARGS) -o {self.y_in} --obj_dir {{obj_dir}} {self.base}
            """)

def build_noop(driver: HammerDriver, append_error_func: Callable[[str], None]) -> dict:
    """
    Do nothing, just return the dependency graph.

    :param driver: The HammerDriver
    :return: The dependency graph
    """
    dependency_graph = driver.get_hierarchical_dependency_graph()
    return dependency_graph

def common_make_text(hier: bool = True) -> textwrap.dedent:
    actions = [
        MakeActionRecipe("sim-rtl", "{p_sim_rtl_in}", "{syn_deps}", hier=hier),
        MakeActionRecipe("syn", "{p_syn_in}", "{syn_deps}", hier=hier),
        MakeLinkRecipe("syn-to-sim", hier=hier),
        MakeActionRecipe("sim-syn", hier=hier),
        MakeLinkRecipe("syn-to-par", hier=hier),
        MakeActionRecipe("par", hier=hier),
        MakeLinkRecipe("par-to-sim", hier=hier),
        MakeActionRecipe("sim-par", hier=hier),
        MakeLinkRecipe("sim-par-to-power", hier=hier),
        MakeLinkRecipe("par-to-power", hier=hier),
        MakeActionRecipe("power-par", hier=hier),
        MakeLinkRecipe("sim-rtl-to-power", hier=hier),
        MakeActionRecipe("power-rtl", hier=hier),
        MakeLinkRecipe("sim-syn-to-power", hier=hier),
        MakeLinkRecipe("syn-to-power", hier=hier),
        MakeActionRecipe("power-syn", hier=hier),
        MakeLinkRecipe("par-to-drc", hier=hier),
        MakeActionRecipe("drc", hier=hier),
        MakeLinkRecipe("par-to-lvs", hier=hier),
        MakeActionRecipe("lvs", hier=hier),
        MakeLinkRecipe("syn-to-formal", hier=hier),
        MakeActionRecipe("formal-syn", hier=hier),
        MakeLinkRecipe("par-to-formal", hier=hier),
        MakeActionRecipe("formal-par", hier=hier),
        MakeLinkRecipe("syn-to-timing", hier=hier),
        MakeActionRecipe("timing-syn", hier=hier),
        MakeLinkRecipe("par-to-timing", hier=hier),
        MakeActionRecipe("timing-par", hier=hier)
    ]

    make_text = textwrap.dedent("""
            ####################################################################################
            ## Steps for {mod}
            ####################################################################################
            """)
    make_text += ".PHONY: " + " ".join([a.action + "{suffix}" for a in actions]) + "\n\n"
    make_text += "\n".join([a.phony_target() for a in actions]) + "\n\n"
    make_text += "\n".join([a.recipe() for a in actions]) + "\n\n"
    make_text += textwrap.dedent("""
            # Redo steps
            # These intentionally break the dependency graph, but allow the flexibility to rerun a step after changing a config.
            # Hammer doesn't know what settings impact synthesis only, e.g., so these are for power-users who "know better."
            # The HAMMER_EXTRA_ARGS variable allows patching in of new configurations with -p or using flow control (--to_step or --from_step), for example.
            """)
    make_text += ".PHONY: " + " ".join(["redo-" + a.action + "{suffix}" for a in actions]) + "\n\n"
    make_text += "\n".join([a.redo_recipe() for a in actions]) + "\n\n"
    if hier:
        make_text += "{par_to_syn}\n\n"
    return make_text

def top_down_nonleaf_make_text() -> textwrap.dedent:
    """
    If non-leaf node, par is broken up into two separate actions:
        par-partition-{suffix}
        par-assemble-{suffix}
    """
    actions = [
        MakeActionRecipe("sim-rtl", "{p_sim_rtl_in}", "{syn_deps}"),
        MakeActionRecipe("syn", "{p_syn_in}", "{syn_deps}"),
        MakeLinkRecipe("syn-to-sim"),
        MakeActionRecipe("sim-syn"),
        MakeLinkRecipe("syn-to-par"),
        MakeActionRecipe("par-partition"),
        MakeActionRecipe("par-assemble"),
        #MakeLinkRecipe("par-partition-to-par"),
        #MakeLinkRecipe("par-to-par-assemble"),
        MakeLinkRecipe("par-to-sim"),
        MakeActionRecipe("sim-par"),
        MakeLinkRecipe("sim-par-to-power"),
        MakeLinkRecipe("par-to-power"),
        MakeActionRecipe("power-par"),
        MakeLinkRecipe("sim-rtl-to-power"),
        MakeActionRecipe("power-rtl"),
        MakeLinkRecipe("sim-syn-to-power"),
        MakeLinkRecipe("syn-to-power"),
        MakeActionRecipe("power-syn"),
        MakeLinkRecipe("par-to-drc"),
        MakeActionRecipe("drc"),
        MakeLinkRecipe("par-to-lvs"),
        MakeActionRecipe("lvs"),
        MakeLinkRecipe("syn-to-formal"),
        MakeActionRecipe("formal-syn"),
        MakeLinkRecipe("par-to-formal"),
        MakeActionRecipe("formal-par"),
        MakeLinkRecipe("syn-to-timing"),
        MakeActionRecipe("timing-syn"),
        MakeLinkRecipe("par-to-timing"),
        MakeActionRecipe("timing-par")
    ]

    """
                    if top node
                        {par_partition_in}: {par_in}
            {par_partition_in}: {prereqs} ==> prereqs == par_partition_out from the previous level
            \t$(HAMMER_EXEC) {env_confs} -p {prereqs} $(HAMMER_EXTRA_ARGS) -o {par_in} --obj_dir {obj_dir} syn-to-par

            {par_assemble_in}: {prereqs} ==> prereqs == par_assemble_out or par_out from the previous level
            \t$(HAMMER_EXEC) {env_confs} -p {prereqs} $(HAMMER_EXTRA_ARGS) -o {par_in} --obj_dir {obj_dir} syn-to-par

            {par_partition_out}: {par_partition_in} $(HAMMER_PAR_DEPENDENCIES)
            \t$(HAMMER_EXEC) {env_confs} -p {par_partition_in} $(HAMMER_EXTRA_ARGS) --obj_dir {obj_dir} par{suffix}

            {par_assemble_out}: {par_assemble_in} $(HAMMER_PAR_DEPENDENCIES)
            \t$(HAMMER_EXEC) {env_confs} -p {par_assemble_in} $(HAMMER_EXTRA_ARGS) --obj_dir {obj_dir} par{suffix}

    """

    make_text = textwrap.dedent("""
            ####################################################################################
            ## Steps for {mod}
            ####################################################################################
            """)
    make_text += ".PHONY: " + " ".join([a.action + "{suffix}" for a in actions]) + "\n\n"
    make_text += "\n".join([a.phony_target() for a in actions]) + "\n\n"
    make_text += "\n".join([a.recipe() for a in actions]) + "\n\n"
    make_text += textwrap.dedent("""
            # Redo steps
            # These intentionally break the dependency graph, but allow the flexibility to rerun a step after changing a config.
            # Hammer doesn't know what settings impact synthesis only, e.g., so these are for power-users who "know better."
            # The HAMMER_EXTRA_ARGS variable allows patching in of new configurations with -p or using flow control (--to_step or --from_step), for example.
            """)
    make_text += ".PHONY: " + " ".join(["redo-" + a.action + "{suffix}" for a in actions]) + "\n\n"
    make_text += "\n".join([a.redo_recipe() for a in actions]) + "\n\n"
    return make_text


def top_down_leaf_make_text() -> textwrap.dedent:
    """
    If leaf node, par depends on the parent's par-partition
    """
    actions = [
        MakeActionRecipe("sim-rtl", "{p_sim_rtl_in}", "{syn_deps}"),
        MakeActionRecipe("syn", "{p_syn_in}", "{syn_deps}"),
        MakeLinkRecipe("syn-to-sim"),
        MakeActionRecipe("sim-syn"),
        MakeLinkRecipe("syn-to-par"),
        MakeLinkRecipe("par-partition-to-par"),
        MakeActionRecipe("par", "{p_par_in}"),
        MakeLinkRecipe("par-to-sim"),
        MakeActionRecipe("sim-par"),
        MakeLinkRecipe("sim-par-to-power"),
        MakeLinkRecipe("par-to-power"),
        MakeActionRecipe("power-par"),
        MakeLinkRecipe("sim-rtl-to-power"),
        MakeActionRecipe("power-rtl"),
        MakeLinkRecipe("sim-syn-to-power"),
        MakeLinkRecipe("syn-to-power"),
        MakeActionRecipe("power-syn"),
        MakeLinkRecipe("par-to-drc"),
        MakeActionRecipe("drc"),
        MakeLinkRecipe("par-to-lvs"),
        MakeActionRecipe("lvs"),
        MakeLinkRecipe("syn-to-formal"),
        MakeActionRecipe("formal-syn"),
        MakeLinkRecipe("par-to-formal"),
        MakeActionRecipe("formal-par"),
        MakeLinkRecipe("syn-to-timing"),
        MakeActionRecipe("timing-syn"),
        MakeLinkRecipe("par-to-timing"),
        MakeActionRecipe("timing-par")
    ]

    make_text = textwrap.dedent("""
            ####################################################################################
            ## Steps for {mod}
            ####################################################################################
            """)
    make_text += ".PHONY: " + " ".join([a.action + "{suffix}" for a in actions]) + "\n\n"
    make_text += "\n".join([a.phony_target() for a in actions]) + "\n\n"
    make_text += "\n".join([a.recipe() for a in actions]) + "\n\n"
    make_text += textwrap.dedent("""
            # Redo steps
            # These intentionally break the dependency graph, but allow the flexibility to rerun a step after changing a config.
            # Hammer doesn't know what settings impact synthesis only, e.g., so these are for power-users who "know better."
            # The HAMMER_EXTRA_ARGS variable allows patching in of new configurations with -p or using flow control (--to_step or --from_step), for example.
            """)
    make_text += ".PHONY: " + " ".join(["redo-" + a.action + "{suffix}" for a in actions]) + "\n\n"
    make_text += "\n".join([a.redo_recipe() for a in actions]) + "\n\n"
    return make_text


def build_makefile(driver: HammerDriver, append_error_func: Callable[[str], None]) -> dict:
    """
    Build a Makefile include in the obj_dir called hammer.d. This is intended to be dynamically
    created and included into a top-level Makefile.

    The Makefile will contain targets for the following hammer actions, as well as any necessary
    bridge actions (xyz-to-abc):
        - pcb
        - syn
        - par
        - drc
        - lvs
        - sim-rtl
        - sim-syn
        - sim-par
        - power-rtl
        - power-syn
        - power-par
        - formal-syn
        - formal-par
        - timing-syn
        - timing-par

    For hierarchical flows, the syn, par, drc, lvs, sim, power, formal, and timing actions will all be suffixed with the name
    of the hierarchical modules (e.g. syn-Top, syn-SubModA, par-SubModA, etc.). The appropriate
    dependencies and bridge actions are automatically generated from the hierarchy provided in the
    Hammer IR.

    For actions that can be run at multiple points in the flow such as sim, the name of the target
    will include the action it is being run after (e.g. sim-syn, sim-par, etc.). With no suffix
    an rtl level simulation will be run.

    Additionally, "redo" steps are created (e.g. redo-par for flat designs or redo-par-Top for
    hierarchical), which allow the user to bypass the normal Makefile dependencies and force a
    rerun of a particular task. This is useful when the user wants to change an input Hammer IR file
    knowing it will not affect intermediate steps in the design.

    An example use case for integrating this file into a top flow is provided below. Be sure to use
    real tabs if copying this snippet!

    ```
    TOP ?= MyTop
    OBJ_DIR ?= $(abspath build-$(TOP))
    INPUT_CONFS ?= foo.yaml bar.yaml baz.yaml

    HAMMER_EXEC ?= ./mychip-vlsi.py

    .PHONY: all
    all: drc-$(TOP) lvs-$(TOP)

    GENERATED_CONF = $(OBJ_DIR)/input.yaml

    $(GENERATED_CONF):
        echo "synthesis.inputs.top_module: $(TOP)" > $@
        echo "pcb.inputs.top_module: $(TOP)" >> $@

    $(OBJ_DIR)/hammer.d: $(GENERATED_CONF)
        $(HAMMER_EXEC) -e env.yaml $(foreach x,$(INPUT_CONFS) $(GENERATED_CONF), -p $(x)) --obj_dir $(OBJ_DIR) build

    include $(OBJ_DIR)/hammer.mk
    ```

    The generated Makefile has a few variables that are set if absent. This allows the user to override them without
    modifying hammer.mk. They are listed as follows:
        - HAMMER_EXEC: This sets the actual python executable containing the HammerDriver main() function. It is set to
          the executable used to generate the Makefile by default.
        - HAMMER_DEPENDENCIES: The list of dependences to use for the initial syn and pcb targets. It is set to the set
          of all input configurations, environment settings, and input files by default.
        - HAMMER_*_DEPENDENCIES: There is a version of this variable for each action. It allows the user to have more
          fine grained depencies compared to the blunt HAMMER_DEPENDENCIES. It is set as a dependency for the respective
          action. Often used with clearing the global HAMMER_DEPENDENCIES.
        - HAMMER_EXTRA_ARGS: This is passed to the Hammer executable for all targets. This is unset by default.
          Its primary uses are for adding additional configuration files with -p, --to_step/until_step, and/or --from_step/
          after_step options. An example use is "make redo-par-Top HAMMER_EXTRA_ARGS="-p patch.yaml --from_step placement".

    :param driver: The HammerDriver
    :return: The dependency graph
    """

    #modified
    hierarchical_mode = driver.get_user_hierarchical_mode()

    dependency_graph = driver.get_hierarchical_dependency_graph()
    makefile = os.path.join(driver.obj_dir, "hammer.mk")
    os.symlink(makefile, os.path.join(driver.obj_dir, "hammer.d"))
    default_dependencies = driver.options.project_configs + driver.options.environment_configs
    default_dependencies.extend(list(driver.database.get_setting("synthesis.inputs.input_files", [])))
    # Resolve the canonical path for each dependency
    default_dependencies = [os.path.realpath(x) for x in default_dependencies]
    output = "HAMMER_EXEC ?= {}\n".format(os.path.realpath(sys.argv[0]))
    output += "HAMMER_DEPENDENCIES ?= {}\n\n".format(" ".join(default_dependencies))
    syn_deps = "$(HAMMER_DEPENDENCIES)"
    # Get the confs passed into this execution
    env_confs = " ".join(["-e " + os.path.realpath(x) for x in driver.options.environment_configs])
    proj_confs = " ".join(["-p " + os.path.realpath(x) for x in driver.options.project_configs])
    obj_dir = os.path.realpath(driver.obj_dir)

    # Global steps that are the same for hier or flat
    pcb_run_dir = os.path.join(obj_dir, "pcb-rundir")
    pcb_out = os.path.join(pcb_run_dir, "pcb-output-full.json")
    output += textwrap.dedent(f"""
        ####################################################################################
        ## Global steps
        ####################################################################################
        .PHONY: pcb
        pcb: {pcb_out}

        {pcb_out}: {syn_deps}
        \t$(HAMMER_EXEC) {env_confs} {proj_confs} --obj_dir {obj_dir} pcb

        """)

    if not dependency_graph:
        # Flat flow
        top_module = str(driver.database.get_setting("synthesis.inputs.top_module"))
        output += common_make_text(hier=False).format(suffix="", mod=top_module, env_confs=env_confs,
                                   p_sim_rtl_in=proj_confs, p_syn_in=proj_confs, obj_dir=obj_dir,
                                   syn_deps=syn_deps, par_to_syn="")
    else:
        # Top-down hierarchical flow
        if hierarchical_mode == "top_down":
            for node, edges in dependency_graph.items():

                parent_edges = edges[0]

                out_edges = edges[1]

                if len(parent_edges) == 0:  # top node
                    p_sim_rtl_in = proj_confs
                    p_syn_in = proj_confs

                    # need to revert this each time
                    syn_deps = "$(HAMMER_DEPENDENCIES)"

                    output += top_down_nonleaf_make_text.format(
                        suffix="-"+node, mod=node, env_confs=env_confs, obj_dir=obj_dir, syn_deps=syn_deps,
                        p_sim_rtl_in=proj_confs, p_syn_in=p_syn_in)

                elif len(out_edges) == 0:  # leaf node
                    p_sim_rtl_in = proj_confs
                    p_syn_in = proj_confs

                    # # need to revert this each time
                    syn_deps = "$(HAMMER_DEPENDENCIES)"

                    output += top_down_leaf_make_text.format(
                        suffix="-"+node, mod=node, env_confs=env_confs, obj_dir=obj_dir, syn_deps=syn_deps,
                        p_sim_rtl_in=proj_confs, p_syn_in=p_syn_in)

                else:  # hierarchical node
                    p_sim_rtl_in = proj_confs
                    p_syn_in = proj_confs

                    # need to revert this each time
                    syn_deps = "$(HAMMER_DEPENDENCIES)"

                    par_assem_confs = [os.path.join(obj_dir, "par-" + x, "par-output-full.json") if x.database.get_setting("vlsi.inputs.hierarchical.module_mode") == HierarchicalMode.Leaf else os.path.join(obj_dir, "par-assemble-" + x, "par-output-full.json") for x in out_edges]
                    assem_prereqs = " ".join(par_assem_confs)
                    assem_pstring = " ".join(["-p " + x for x in par_assem_confs])
                    par_assemble_out = textwrap.dedent("""
                        {par_assem_deps}: {prereqs}
                        \t$(HAMMER_EXEC) {env_confs} {pstring} -o {syn_deps} --obj_dir {obj_dir} hier-par-to-syn
                        """.format(assem_prereqs=assem_prereqs, env_confs=env_confs, assem_pstring=assem_pstring,
                        obj_dir=obj_dir))


                    output += top_down_nonleaf_make_text.format(
                        suffix="-"+node, mod=node, env_confs=env_confs, obj_dir=obj_dir, syn_deps=syn_deps,
                        p_sim_rtl_in=proj_confs, p_syn_in=p_syn_in)

        # Bottom-up hierarchical flow
        else:
            for node, edges in dependency_graph.items():

                parent_edges = edges[0]

                out_edges = edges[1]

                # need to revert this each time
                syn_deps = "$(HAMMER_DEPENDENCIES)"
                p_syn_in = ""
                par_to_syn = ""

                if len(out_edges) > 0:

                    syn_deps = os.path.join(obj_dir, f"syn-{node}-input.json")
                    p_syn_in = f"-p {syn_deps}"

                    out_confs = [os.path.join(obj_dir, "par-" + x, "par-output-full.json") for x in out_edges]

                    pstring = " ".join(["-p " + x for x in out_confs])
                    par_to_syn = textwrap.dedent(f"""
                        .PHONY: hier-par-to-syn-{node}
                        hier-par-to-syn-{node}: {syn_deps}

                        {syn_deps}: {" ".join(out_confs)}
                        \t$(HAMMER_EXEC) {env_confs} {pstring} -o {syn_deps} --obj_dir {obj_dir} hier-par-to-syn

                        redo-hier-par-to-syn-{node}:
                        \t$(HAMMER_EXEC) {env_confs} {pstring} -o {syn_deps} --obj_dir {obj_dir} hier-par-to-syn
                        """)

                output += common_make_text().format(
                    suffix="-"+node, mod=node, env_confs=env_confs, obj_dir=obj_dir, syn_deps=syn_deps,
                    par_to_syn=par_to_syn, p_sim_rtl_in=proj_confs, p_syn_in=p_syn_in)

    with open(makefile, "w") as f:
        f.write(output)

    return dependency_graph

BuildSystems = {
    "make": build_makefile,
    "none": build_noop
}  # type: Dict[str, Callable[[HammerDriver, Callable[[str], None]], dict]]
