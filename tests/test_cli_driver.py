#  Tests for hammer-vlsi CLIDriver
#
#  See LICENSE for licence details.

import json
import os
from decimal import Decimal
from typing import Any, Callable, Dict, Optional
from pathlib import Path
import importlib.resources as resources

import pytest
import ruamel.yaml

import hammer.config as hammer_config
from hammer.config import HammerJSONEncoder
from hammer.logging.test import HammerLoggingCaptureContext
from hammer.tech import MacroSize
from hammer.vlsi import CLIDriver, HammerDriver
from hammer.vlsi.constraints import PlacementConstraint, PlacementConstraintType
from hammer.utils import deepdict
import hammer.technology.nop as nop_tech
import hammer.synthesis.mocksynth as mocksynth


def syn_rundir(tmpdir: Path) -> str:
    return str(tmpdir / "syn_rundir")


def par_rundir(tmpdir: Path) -> str:
    return str(tmpdir / "par_rundir")


def config_path(tmpdir: Path) -> str:
    return os.path.join(syn_rundir(tmpdir), "run_config.json")


def syn_out_path(tmpdir: Path) -> str:
    return os.path.join(syn_rundir(tmpdir), "syn_out.json")


def par_input_path(tmpdir: Path) -> str:
    return os.path.join(syn_rundir(tmpdir), "par-input.json")


def syn_out_full_path(tmpdir: Path) -> str:
    return os.path.join(syn_rundir(tmpdir), "syn-output-full.json")


def syn_to_par_out_path(tmpdir: Path) -> str:
    return os.path.join(syn_rundir(tmpdir), "syn_par_out.json")

def obj_dir_path(tmpdir: Path) -> str:
    return os.path.join(tmpdir / "obj_dir")

def log_path(tmpdir: Path) -> str:
    return os.path.join(tmpdir / "hammer-vlsi.log")


postprocess_fn_type = Optional[Callable[[Dict[str, Any]], Dict[str, Any]]]
top_module = "dummy"


def generate_dummy_config(tmpdir: Path, postprocessing_func: postprocess_fn_type = None) -> Dict[str, Any]:
    """
    Generate and write a dummy config to the given path.
    :param tmpdir: path to write the dummy config to
    :param postprocessing_func: Optional function to modify/add to the config.
    :return: Config dictionary that was written.
    """
    config = {
        "vlsi.core.technology": "hammer.technology.nop",
        "vlsi.core.synthesis_tool": "hammer.synthesis.mocksynth",
        "vlsi.core.par_tool": "hammer.par.nop",
        "vlsi.inputs.hierarchical.config_source": "none",
        "vlsi.technology.extra_macro_sizes": [],
        "synthesis.inputs.top_module": top_module,
        "synthesis.inputs.input_files": ("/dev/null",),
        "synthesis.mocksynth.temp_folder": syn_rundir(tmpdir)
    }  # type: Dict[str, Any]

    if postprocessing_func is not None:
        config = postprocessing_func(config)

    with open(config_path(tmpdir), "w") as f:
        f.write(json.dumps(config, cls=HammerJSONEncoder, indent=4))

    return config


def set_up_run(tmpdir: Path, postprocessing_fn: postprocess_fn_type = None) -> None:
    """
    Creates the syn and par rundirs and the dummy config,
    """
    os.mkdir(syn_rundir(tmpdir))
    os.mkdir(par_rundir(tmpdir))

    # Generate a config for testing.
    generate_dummy_config(tmpdir, postprocessing_fn)


def run_syn_to_par_with_output(tmpdir: Path) -> None:
    # Check that running the CLIDriver executes successfully (code 0).
    with pytest.raises(SystemExit) as cm:
        CLIDriver().main(args=[
            "syn",  # action
            "-p", config_path(tmpdir),
            "--output", syn_out_path(tmpdir),
            "--syn_rundir", syn_rundir(tmpdir),
            "--par_rundir", par_rundir(tmpdir),
            "--obj_dir", obj_dir_path(tmpdir),
            "--log", log_path(tmpdir)
        ])
    assert cm.value.code == 0
    # Now run syn-to-par with the main config as well as the outputs.
    with pytest.raises(SystemExit) as cm:
        CLIDriver().main(args=[
            "syn-to-par",  # action
            "-p", config_path(tmpdir),
            "-p", syn_out_path(tmpdir),
            "--output", syn_to_par_out_path(tmpdir),
            "--syn_rundir", syn_rundir(tmpdir),
            "--par_rundir", par_rundir(tmpdir),
            "--obj_dir", obj_dir_path(tmpdir),
            "--log", log_path(tmpdir)
        ])
    assert cm.value.code == 0


class TestCLIDriver:

    def test_syn_to_par(self, tmpdir) -> None:
        """ Test that syn-to-par works with the output-only JSON. """
        set_up_run(tmpdir)
        run_syn_to_par_with_output(tmpdir)

        # synthesis output should NOT keep other settings
        with open(syn_out_path(tmpdir), "r") as f:
            syn_output = json.loads(f.read())
            assert syn_output["synthesis.outputs.output_files"] == ["/dev/null"]
            assert "vlsi.core.technology" not in syn_output
        # Generated par input should have other settings
        with open(syn_to_par_out_path(tmpdir), "r") as f:
            par_input = json.loads(f.read())
            assert par_input["par.inputs.top_module"] == top_module
            # par-input should preserve other settings
            assert par_input["vlsi.core.technology"] == "hammer.technology.nop"

    def test_syn_to_par_full(self, tmpdir) -> None:
        """ Test that syn-to-par works with the full JSON. """
        set_up_run(tmpdir)
        run_syn_to_par_with_output(tmpdir)

        # synthesis full output should keep other settings
        with open(syn_out_full_path(tmpdir), "r") as f:
            syn_output = json.loads(f.read())
            assert syn_output["synthesis.outputs.output_files"] == ["/dev/null"]
            assert syn_output["vlsi.core.technology"] == "hammer.technology.nop"
        # Generated par input should have other settings
        with open(syn_to_par_out_path(tmpdir), "r") as f:
            par_input = json.loads(f.read())
            assert par_input["par.inputs.top_module"] == top_module
            # par-input should preserve other settings
            assert par_input["vlsi.core.technology"] == "hammer.technology.nop"

    def test_syn_to_par_improper(self, tmpdir) -> None:
        """
        Test that appropriate error messages are raised when syn-to-par
        is used on a config that does not have outputs.
        """
        set_up_run(tmpdir)
        log_path = os.path.join(syn_rundir(tmpdir), "log.txt")

        with HammerLoggingCaptureContext() as c:
            # Running syn-to-par on a not-output config should fail.
            with pytest.raises(SystemExit) as cm:
                CLIDriver().main(args=[
                    "syn-to-par",  # action
                    "-p", config_path(tmpdir),
                    "--log", log_path,
                    "--output", syn_out_path(tmpdir),
                    "--syn_rundir", syn_rundir(tmpdir),
                    "--par_rundir", par_rundir(tmpdir),
                    "--obj_dir", obj_dir_path(tmpdir),
                ])
            assert cm.value.code == 1
        assert c.log_contains("Input config does not appear to contain valid synthesis outputs")

    def test_syn_to_par_same_as_syn_par(self, tmpdir) -> None:
        """
        Test that syn-par generates the same par input as calling syn,
        syn-to-par.
        """
        set_up_run(tmpdir)
        run_syn_to_par_with_output(tmpdir)

        # Run syn-par
        with pytest.raises(SystemExit) as cm:
            CLIDriver().main(args=[
                "syn-par",  # action
                "-p", config_path(tmpdir),
                "--syn_rundir", syn_rundir(tmpdir),
                "--par_rundir", par_rundir(tmpdir),
                "--obj_dir", obj_dir_path(tmpdir),
                "--log", log_path(tmpdir),
                "--output", syn_out_path(tmpdir),
            ])
            assert cm.value.code == 0

        # Check that the syn-to-par generated par input and the syn-par
        # generated par input are the same, modulo any synthesis.outputs.*
        # settings since they don't matter for par input.
        with open(syn_to_par_out_path(tmpdir), "r") as f:
            with open(par_input_path(tmpdir), "r") as f2:
                syn_to_par_output = json.loads(f.read())
                syn_to_par_output = dict(filter(lambda i: "synthesis.outputs." not in i[0], syn_to_par_output.items()))
                syn_par_output = json.loads(f2.read())
                syn_par_output = dict(filter(lambda i: "synthesis.outputs." not in i[0], syn_par_output.items()))
                assert syn_to_par_output == syn_par_output

    def test_syn_par_config_dumping(self, tmpdir) -> None:
        """
        Test that the syn_par step (running both synthesis and place-and-route) dumps the intermediate config files,
        namely synthesis output config and par input config.
        """
        set_up_run(tmpdir)

        # Check that running the CLIDriver executes successfully (code 0).
        with pytest.raises(SystemExit) as cm:
            CLIDriver().main(args=[
                "syn-par",  # action
                "-p", config_path(tmpdir),
                "--output", syn_out_path(tmpdir),
                "--syn_rundir", syn_rundir(tmpdir),
                "--par_rundir", par_rundir(tmpdir),
                "--obj_dir", obj_dir_path(tmpdir),
                "--log", log_path(tmpdir)
            ])
        assert cm.value.code == 0

        # Check that the synthesis output and par input configs got dumped.
        with open(tmpdir / "syn_rundir" / "syn-output.json", "r") as f:
            syn_output = json.loads(f.read())
            assert syn_output["synthesis.outputs.output_files"] == ["/dev/null"]
            # syn-output should NOT keep other settings
            assert "vlsi.core.technology" not in syn_output
        with open(syn_out_full_path(tmpdir), "r") as f:
            syn_output_full = json.loads(f.read())
            assert syn_output_full["synthesis.outputs.output_files"] == ["/dev/null"]
            # syn-output-full should preserve other settings
            assert syn_output_full["vlsi.core.technology"] == "hammer.technology.nop"
        with open(par_input_path(tmpdir), "r") as f:
            par_input = json.loads(f.read())
            assert par_input["par.inputs.top_module"] == top_module
            # par-input should preserve other settings
            assert par_input["vlsi.core.technology"] == "hammer.technology.nop"

    def test_dump(self, tmpdir) -> None:
        """ Test that dump works properly. """
        set_up_run(tmpdir)

        config_unpacked_path = os.path.join(syn_rundir(tmpdir), "run_config_unpacked.json")
        # Equivalent config to above but not unpacked
        with open(config_path(tmpdir), "r") as f:
            unpacked_config = hammer_config.reverse_unpack(json.loads(f.read()))
        with open(config_unpacked_path, "w") as f:
            f.write(json.dumps(unpacked_config, cls=HammerJSONEncoder, indent=4))

        # Check that running the CLIDriver executes successfully (code 0).
        with pytest.raises(SystemExit) as cm:
            CLIDriver().main(args=[
                "dump",  # action
                "-p", config_unpacked_path,
                "--output", syn_out_path(tmpdir),
                "--syn_rundir", syn_rundir(tmpdir),
                "--par_rundir", syn_rundir(tmpdir),
                "--obj_dir", obj_dir_path(tmpdir),
                "--log", log_path(tmpdir)
            ])
        assert cm.value.code == 0

        # Check that dumped output should be same as what we read in.
        with open(syn_out_path(tmpdir), "r") as f:
            dumped_output = json.loads(f.read())
        with open(config_path(tmpdir), "r") as f:
            packed_output = json.loads(f.read())
        assert packed_output == dumped_output

    def test_hier_dump(self, tmpdir) -> None:
        """ Test that hierarchical settings work properly. """

        def add_hier(d: Dict[str, Any]) -> Dict[str, Any]:
            output = deepdict(d)
            dummy_placement = PlacementConstraint(
                path="dummy",
                type=PlacementConstraintType.Dummy,
                x=Decimal("0"),
                y=Decimal("0"),
                width=Decimal("10"),
                height=Decimal("10"),
                master=None,
                create_physical=None,
                orientation=None,
                margins=None,
                top_layer=None,
                layers=None,
                obs_types=None).to_dict()
            output["vlsi.inputs.default_output_load"] = 1
            output["vlsi.inputs.hierarchical.top_module"] = top_module
            output["vlsi.inputs.hierarchical.flat"] = "hierarchical"
            output["vlsi.inputs.hierarchical.config_source"] = "manual"
            output["vlsi.inputs.hierarchical.manual_modules"] = [
                {"mod1": ["m1s1", "m1s2"], "mod2": ["m2s1"], top_module: ["mod1", "mod2"]}]
            manual_constraints = [{"mod1": [dummy_placement]},
                                  {"mod2": [dummy_placement]},
                                  {"m1s1": [dummy_placement]},
                                  {"m1s2": [dummy_placement]},
                                  {"m2s1": [dummy_placement]},
                                  {top_module: [dummy_placement]}]
            output["vlsi.inputs.hierarchical.manual_placement_constraints"] = manual_constraints
            output["vlsi.inputs.hierarchical.constraints"] = [{"mod1": [{"vlsi.inputs.default_output_load": 2}]},
                                                              {"m2s1": [{"vlsi.inputs.default_output_load": 3}]}]
            return output

        set_up_run(tmpdir, add_hier)

        # Check that running the CLIDriver executes successfully (code 0).
        with pytest.raises(SystemExit) as cm:
            CLIDriver().main(args=[
                "auto",  # action
                "-p", config_path(tmpdir),
                "--obj_dir", syn_rundir(tmpdir),
                "--log", log_path(tmpdir),
                "--output", str(tmpdir / "output.json")
            ])
        assert cm.value.code == 0

        # Check that dumped output should be same as what we read in.
        with open(os.path.join(syn_rundir(tmpdir), "syn-m2s1/full_config.json"), "r") as f:
            dumped_output = json.loads(f.read())
        assert dumped_output['vlsi.inputs.default_output_load'] == 3
        with open(os.path.join(syn_rundir(tmpdir), "syn-m1s1/full_config.json"), "r") as f:
            dumped_output = json.loads(f.read())
        assert dumped_output['vlsi.inputs.default_output_load'] == 1
        with open(os.path.join(syn_rundir(tmpdir), "syn-mod1/full_config.json"), "r") as f:
            dumped_output = json.loads(f.read())
        assert dumped_output['vlsi.inputs.default_output_load'] == 2

    def test_hier_dump_empty_constraints(self, tmpdir) -> None:
        """
        Test that hierarchical settings work properly even when no constraints
        are given.
        """

        def add_hier(d: Dict[str, Any]) -> Dict[str, Any]:
            output = deepdict(d)
            output["vlsi.inputs.default_output_load"] = 1
            output["vlsi.inputs.hierarchical.top_module"] = top_module
            output["vlsi.inputs.hierarchical.flat"] = "hierarchical"
            output["vlsi.inputs.hierarchical.config_source"] = "manual"
            output["vlsi.inputs.hierarchical.manual_modules"] = [
                {"mod1": ["m1s1", "m1s2"], "mod2": ["m2s1"], top_module: ["mod1", "mod2"]}]
            output["vlsi.inputs.hierarchical.manual_placement_constraints"] = []
            output["vlsi.inputs.hierarchical.constraints"] = []
            return output

        set_up_run(tmpdir, add_hier)

        # Check that running the CLIDriver executes successfully (code 0).
        with pytest.raises(SystemExit) as cm:
            CLIDriver().main(args=[
                "auto",  # action
                "-p", config_path(tmpdir),
                "--obj_dir", syn_rundir(tmpdir),
                "--log", log_path(tmpdir),
                "--output", str(tmpdir / "output.json")
            ])
        assert cm.value.code == 0

    def test_dump_macrosizes(self, tmpdir) -> None:
        """ Test that dump-macrosizes works properly. """

        my_size = MacroSize(
            library='my_lib',
            name='my_cell',
            width=Decimal("100"),
            height=Decimal("100")
        )

        def add_macro_sizes(d: Dict[str, Any]) -> Dict[str, Any]:
            output = deepdict(d)
            output["vlsi.technology.extra_macro_sizes"] = [my_size.to_setting()]
            return output

        set_up_run(tmpdir, add_macro_sizes)

        # Check that running the CLIDriver executes successfully (code 0).
        with pytest.raises(SystemExit) as cm:
            CLIDriver().main(args=[
                "dump-macrosizes",  # action
                "-p", config_path(tmpdir),
                "--output", syn_out_path(tmpdir),
                "--syn_rundir", syn_rundir(tmpdir),
                "--par_rundir", syn_rundir(tmpdir),
                "--obj_dir", obj_dir_path(tmpdir),
                "--log", log_path(tmpdir)
            ])
        assert cm.value.code == 0

        # Check that dumped output should be same as what we read in.
        with open(syn_out_path(tmpdir), "r") as f:
            dumped_output = json.loads(f.read())
            assert dumped_output == [my_size.to_setting()]

    def test_override_actions(self, tmpdir) -> None:
        """ Test that we can override actions like synthesis_action etc in subclasses. """

        class OverriddenDriver(CLIDriver):
            synthesis_called = False  # type: bool

            def synthesis_action(self, driver: HammerDriver,
                                 append_error_func: Callable[[str], None]) -> Optional[Dict]:
                def post_run_func(driver: HammerDriver) -> None:
                    OverriddenDriver.synthesis_called = True

                return self.create_action(action_type="synthesis", extra_hooks=None, post_run_func=post_run_func)(
                    driver, append_error_func)

        set_up_run(tmpdir)

        # Check that running the CLIDriver executes successfully (code 0).
        with pytest.raises(SystemExit) as cm:
            OverriddenDriver().main(args=[
                "syn",  # action
                "-p", config_path(tmpdir),
                "--syn_rundir", syn_rundir(tmpdir),
                "--par_rundir", syn_rundir(tmpdir),
                "--obj_dir", obj_dir_path(tmpdir),
                "--log", log_path(tmpdir),
                "--output", syn_out_path(tmpdir),
            ])
        assert cm.value.code == 0

        # Check that our synthesis function got called.
        assert OverriddenDriver.synthesis_called is True

    def test_bad_override(self) -> None:
        """Test that a bad override of e.g. synthesis_action is caught."""
        with pytest.raises(TypeError):
            class BadOverride(CLIDriver):
                def synthesis_action(self, bad: int) -> dict:  # type: ignore
                    return {bad: "bad"}
            BadOverride()

    def test_key_history(self, tmp_path) -> None:
        """Test that a key history file is created using synthesis."""

        set_up_run(tmp_path)
        history_path = os.path.join(syn_rundir(tmp_path), "syn-output-history.yml")
        run_syn_to_par_with_output(tmp_path)

        # History file should have comments
        with open(config_path(tmp_path), 'r') as f:
            config = json.load(f)

        with open(history_path, 'r') as f:
            yaml = ruamel.yaml.YAML()
            data = yaml.load(f)
            for i in config.keys():
                cmt = data.ca.items[i][2]
                assert cmt.value == f"# Modified by: {config_path(tmp_path)}\n"

    def test_key_history_as_input(self, tmp_path) -> None:
        """Test that a key history file is created using synthesis."""

        set_up_run(tmp_path)
        history_path = os.path.join(syn_rundir(tmp_path), "syn-output-history.yml")

        # Check that running the CLIDriver executes successfully (code 0).
        with pytest.raises(SystemExit) as cm:
            CLIDriver().main(args=[
                "syn",  # action
                "-p", config_path(tmp_path),
                "--output", syn_out_path(tmp_path),
                "--syn_rundir", syn_rundir(tmp_path),
                "--obj_dir", obj_dir_path(tmp_path),
                "--log", log_path(tmp_path)
            ])
        assert cm.value.code == 0

        # Now run par with the main config as well as the outputs.
        with pytest.raises(SystemExit) as cm:
            CLIDriver().main(args=[
                "syn-to-par",  # action
                "-p", config_path(tmp_path),
                "-p", history_path,
                "--output", syn_to_par_out_path(tmp_path),
                "--syn_rundir", syn_rundir(tmp_path),
                "--par_rundir", par_rundir(tmp_path),
                "--obj_dir", obj_dir_path(tmp_path),
                "--log", log_path(tmp_path)
            ])
        assert cm.value.code == 0
