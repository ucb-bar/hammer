#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer_build_systems.py
#  Class containing all the methods to create VLSI flow build system infrastructure
#
#  See LICENSE for licence details.

from .driver import HammerDriver

import os
import sys
import textwrap
from typing import List, Dict, Tuple, Callable

def build_noop(driver: HammerDriver) -> dict:
    """
    Do nothing, just return the dependency graph.

    :param driver: The HammerDriver
    :return: The dependency graph
    """
    dependency_graph = driver.get_hierarchical_dependency_graph()
    return dependency_graph


def build_makefile(driver: HammerDriver) -> dict:
    """
    Build a Makefile include in the obj_dir called hammer.d. This is intended to be dynamically
    created and included into a top-level Makefile.

    :param driver: The HammerDriver
    :return: The dependency graph
    """
    dependency_graph = driver.get_hierarchical_dependency_graph()
    makefile = os.path.join(driver.obj_dir, "hammer.d")
    default_dependencies = driver.options.project_configs + driver.options.environment_configs
    default_dependencies.extend(list(driver.database.get_setting("synthesis.inputs.input_files", [])))
    # Resolve the canonical path for each dependency
    default_dependencies = [os.path.realpath(x) for x in default_dependencies]
    output = "HAMMER_EXEC ?= {}\n".format(os.path.realpath(sys.argv[0]))
    output += "HAMMER_DEPENDENCIES ?= {}\n\n".format(" ".join(default_dependencies))
    deps = "$(HAMMER_DEPENDENCIES)"
    # Get the confs passed into this execution
    env_confs = " ".join(["-e " + os.path.realpath(x) for x in driver.options.environment_configs])
    proj_confs = " ".join(["-p " + os.path.realpath(x) for x in driver.options.project_configs])
    obj_dir = os.path.realpath(driver.obj_dir)

    # Global steps that are the same for hier or flat
    pcb_run_dir = os.path.join(obj_dir, "pcb-rundir")
    pcb_out = os.path.join(pcb_run_dir, "pcb-output.json")
    output += textwrap.dedent("""
        ####################################################################################
        ## Global steps
        ####################################################################################
        .PHONY: pcb
        pcb: {pcb_out}

        {pcb_out}: {deps}
        \t$(HAMMER_EXEC) {env_confs} {syn_in} --obj_dir {obj_dir} pcb

        """.format(pcb_out=pcb_out, deps=deps, env_confs=env_confs, syn_in=proj_confs, obj_dir=obj_dir))

    make_text = textwrap.dedent("""
        ####################################################################################
        ## Steps for {mod}
        ####################################################################################
        .PHONY: syn{suffix} par{suffix} drc{suffix} lvs{suffix}
        syn{suffix}: {syn_out}
        par{suffix}: {par_out}
        drc{suffix}: {drc_out}
        lvs{suffix}: {lvs_out}

        {syn_out}: {deps}
        \t$(HAMMER_EXEC) {env_confs} {syn_in} --obj_dir {obj_dir} syn{suffix}

        {par_in}: {syn_out}
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {syn_out} -o {par_in} --obj_dir {obj_dir} syn-to-par

        {par_out}: {par_in}
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {par_in} --obj_dir {obj_dir} par{suffix}

        {drc_in}: {par_out}
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {par_out} -o {drc_in} --obj_dir {obj_dir} par-to-drc

        {drc_out}: {drc_in}
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {drc_in} --obj_dir {obj_dir} drc{suffix}

        {lvs_in}: {par_out}
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {par_out} -o {lvs_in} --obj_dir {obj_dir} par-to-lvs

        {lvs_out}: {lvs_in}
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {lvs_in} --obj_dir {obj_dir} lvs{suffix}

        # Redo steps
        # These intentionally break the dependency graph, but allow the flexibility to rerun a step after changing a config.
        # Hammer doesn't know what settings impact synthesis only, e.g., so these are for power-users who "know better."
        .PHONY: redo-syn{suffix} redo-par{suffix} redo-drc{suffix} redo-lvs{suffix}

        redo-syn{suffix}:
        \t$(HAMMER_EXEC) {env_confs} {syn_in} --obj_dir {obj_dir} syn{suffix}

        redo-par{suffix}:
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {par_in} --obj_dir {obj_dir} par{suffix}

        redo-drc{suffix}:
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {drc_in} --obj_dir {obj_dir} drc{suffix}

        redo-lvs{suffix}:
        \t$(HAMMER_EXEC) {env_confs} {syn_in} -p {lvs_in} --obj_dir {obj_dir} lvs{suffix}

        """)

    if not dependency_graph:
        # Flat flow
        top_module = str(driver.database.get_setting("synthesis.inputs.top_module"))

        # TODO make this DRY
        syn_run_dir = os.path.join(obj_dir, "syn-rundir")
        par_run_dir = os.path.join(obj_dir, "par-rundir")
        drc_run_dir = os.path.join(obj_dir, "drc-rundir")
        lvs_run_dir = os.path.join(obj_dir, "lvs-rundir")

        syn_in = proj_confs
        syn_out = os.path.join(syn_run_dir, "syn-output.json")
        par_in = os.path.join(obj_dir, "par-input.json")
        par_out = os.path.join(par_run_dir, "par-output.json")
        drc_in = os.path.join(obj_dir, "drc-input.json")
        drc_out = os.path.join(drc_run_dir, "drc-output.json")
        lvs_in = os.path.join(obj_dir, "lvs-input.json")
        lvs_out = os.path.join(lvs_run_dir, "lvs-output.json")

        output += make_text.format(suffix="", mod=top_module, env_confs=env_confs, obj_dir=obj_dir, deps=deps,
            syn_in=syn_in, syn_out=syn_out, par_in=par_in, par_out=par_out,
            drc_in=drc_in, drc_out=drc_out, lvs_in=lvs_in, lvs_out=lvs_out)
    else:
        # Hierarchical flow
        for node, edges in dependency_graph.items():
            out_edges = edges[1]
            # need to revert this each time
            deps = "$(HAMMER_DEPENDENCIES)"
            if len(out_edges) > 0:
                deps = " ".join(["par-" + x for x in out_edges])

            # TODO make this DRY
            syn_run_dir = os.path.join(obj_dir, "syn-" + node)
            par_run_dir = os.path.join(obj_dir, "par-" + node)
            drc_run_dir = os.path.join(obj_dir, "drc-" + node)
            lvs_run_dir = os.path.join(obj_dir, "lvs-" + node)

            syn_in = proj_confs
            syn_out = os.path.join(syn_run_dir, "syn-output.json")
            par_in = os.path.join(obj_dir, "par-{}-input.json".format(node))
            par_out = os.path.join(par_run_dir, "par-output.json")
            drc_in = os.path.join(obj_dir, "drc-{}-input.json".format(node))
            drc_out = os.path.join(drc_run_dir, "drc-output.json")
            lvs_in = os.path.join(obj_dir, "lvs-{}-input.json".format(node))
            lvs_out = os.path.join(lvs_run_dir, "lvs-output.json")

            output += make_text.format(suffix="-"+node, mod=node, env_confs=env_confs, obj_dir=obj_dir, deps=deps,
                syn_in=syn_in, syn_out=syn_out, par_in=par_in, par_out=par_out,
                drc_in=drc_in, drc_out=drc_out, lvs_in=lvs_in, lvs_out=lvs_out)

    with open(makefile, "w") as f:
        f.write(output)

    return dependency_graph

BuildSystems = {
    "make": build_makefile,
    "none": build_noop
}  # type: Dict[str, Callable[[HammerDriver], dict]]
