import json
import os
from typing import Optional, Callable, Iterator

from pydantic import BaseModel
import pytest

from hammer import vlsi as hammer_vlsi
from hammer.config import HammerJSONEncoder
from hammer.logging.test import HammerLoggingCaptureContext
from hammer.vlsi.hooks import HammerStartStopStep


class HooksTestContext(BaseModel):
    temp_dir: str
    driver: Optional[hammer_vlsi.HammerDriver]

    class Config:
        arbitrary_types_allowed = True


@pytest.fixture()
def test_context(tmp_path) -> Iterator[HooksTestContext]:
    """Initialize context by creating the temp_dir, driver, and loading mocksynth."""
    temp_dir = str(tmp_path)
    json_path = os.path.join(temp_dir, "project.json")
    with open(json_path, "w") as f:
        f.write(json.dumps({
            "vlsi.core.synthesis_tool": "hammer.synthesis.mocksynth",
            "vlsi.core.technology": "hammer.technology.nop",
            "synthesis.inputs.top_module": "dummy",
            "synthesis.inputs.input_files": ("/dev/null",),
            "synthesis.mocksynth.temp_folder": temp_dir
        }, cls=HammerJSONEncoder, indent=4))
    options = hammer_vlsi.HammerDriverOptions(
        environment_configs=[],
        project_configs=[json_path],
        log_file=os.path.join(temp_dir, "log.txt"),
        obj_dir=temp_dir
    )
    driver = hammer_vlsi.HammerDriver(options)
    driver.load_synthesis_tool()
    yield HooksTestContext(temp_dir=str(tmp_path), driver=driver)


def change1(x: hammer_vlsi.HammerTool) -> bool:
    x.set_setting("synthesis.mocksynth.step1", "HelloWorld")
    return True


def change2(x: hammer_vlsi.HammerTool) -> bool:
    x.set_setting("synthesis.mocksynth.step2", "HelloWorld")
    return True


def change3(x: hammer_vlsi.HammerTool) -> bool:
    x.set_setting("synthesis.mocksynth.step3", "HelloWorld")
    return True


def change4(x: hammer_vlsi.HammerTool) -> bool:
    x.set_setting("synthesis.mocksynth.step4", "HelloWorld")
    return True


def persist_hook(tmpdir: str) -> Callable[[hammer_vlsi.HammerTool], bool]:
    def persist(x: hammer_vlsi.HammerTool) -> bool:
        file1 = os.path.join(tmpdir, "persist.txt")
        with open(file1, "w") as f:
            f.write("HelloWorld")
        return True
    return persist


def persist_hook2(tmpdir: str) -> Callable[[hammer_vlsi.HammerTool], bool]:
    def persist2(x: hammer_vlsi.HammerTool) -> bool:
        file2 = os.path.join(tmpdir, "persist2.txt")
        with open(file2, "w") as f:
            f.write("ByeByeWorld")
        return True
    return persist2


class TestHammerToolHooks:
    @staticmethod
    def read(filename: str) -> str:
        with open(filename, "r") as f:
            return f.read()

    def test_normal_execution(self, test_context) -> None:
        """Test that no hooks means that everything is executed properly."""
        success, syn_output = test_context.driver.run_synthesis()
        assert success

        for i in range(1, 5):
            assert self.read(os.path.join(test_context.temp_dir, "step{}.txt".format(i))) == \
                "step{}".format(i)

    def test_replacement_hooks(self, test_context) -> None:
        """Test that replacement hooks work."""
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_removal_hook("step2"),
            hammer_vlsi.HammerTool.make_removal_hook("step4")
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i == 2 or i == 4:
                assert not os.path.exists(file)
            else:
                assert self.read(file) == "step{}".format(i)

    def test_resume_hooks(self, test_context) -> None:
        """Test that resume hooks work."""
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_resume_hook("step3")
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i <= 2:
                assert not os.path.exists(file), "step{}.txt should not exist".format(i)
            else:
                assert self.read(file) == "step{}".format(i)

        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_resume_hook("step2")
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i <= 2:
                assert not os.path.exists(file), "step{}.txt should not exist".format(i)
            else:
                assert self.read(file) == "step{}".format(i)

    def test_pause_hooks(self, test_context) -> None:
        """Test that pause hooks work."""
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_pause_hook("step3")
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i > 2:
                assert not os.path.exists(file)
            else:
                assert self.read(file) == "step{}".format(i)

        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_pause_hook("step3")
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i > 3:
                assert not os.path.exists(file)
            else:
                assert self.read(file) == "step{}".format(i)

    def test_pause_hooks_logging(self, test_context) -> None:
        """Test that pause hooks log correctly."""
        with HammerLoggingCaptureContext() as c2:
            success, syn_output = test_context.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_post_pause_hook("step1")
            ])
            assert success

        # step2 to step4 should show up in log as skipped
        for i in range(2, 5):
            assert c2.log_contains("Sub-step 'step{}' skipped due to pause hook".format(i))
        # step1 should NOT show up in log as skipped
        assert not c2.log_contains("Sub-step 'step1' skipped due to pause hook")

    def test_extra_pause_hooks(self, test_context) -> None:
        """Test that extra pause hooks cause an error."""
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_pause_hook("step3"),
            hammer_vlsi.HammerTool.make_post_pause_hook("step3")
        ])
        assert not success

    def test_insertion_hooks(self, test_context) -> None:
        """Test that insertion hooks work."""
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_insertion_hook("step3", change3)
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i == 3:
                assert self.read(file) == "HelloWorld"
            else:
                assert self.read(file) == "step{}".format(i)

    def test_insertion_hooks2(self, test_context) -> None:
        # Test inserting before the first step
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_insertion_hook("step1", change1)
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i == 1:
                assert self.read(file) == "HelloWorld"
            else:
                assert self.read(file) == "step{}".format(i)

    def test_insertion_hooks3(self, test_context) -> None:
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_insertion_hook("step2", change2),
            hammer_vlsi.HammerTool.make_post_insertion_hook("step3", change3),
            hammer_vlsi.HammerTool.make_pre_insertion_hook("change3", change4)
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i == 2 or i == 4:
                assert self.read(file) == "HelloWorld"
            else:
                assert self.read(file) == "step{}".format(i)

    def test_bad_hooks(self, test_context) -> None:
        """Test that hooks with bad targets are errors."""
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_removal_hook("does_not_exist")
        ])
        assert not success

        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_removal_hook("free_lunch")
        ])
        assert not success

        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_removal_hook("penrose_stairs")
        ])
        assert not success

    def test_insert_before_first_step(self, test_context) -> None:
        """Test that inserting a step before the first step works."""
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_insertion_hook("step1", change3)
        ])
        assert success

        for i in range(1, 5):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i == 3:
                assert self.read(file) == "HelloWorld"
            else:
                assert self.read(file) == "step{}".format(i)

    def test_resume_pause_hooks_with_custom_steps(self, test_context) -> None:
        """Test that resume/pause hooks work with custom steps."""

        def step5(x: hammer_vlsi.HammerTool) -> bool:
            with open(os.path.join(test_context.temp_dir, "step5.txt"), "w") as f:
                f.write("HelloWorld")
            return True

        def step6(x: hammer_vlsi.HammerTool) -> bool:
            with open(os.path.join(test_context.temp_dir, "step6.txt"), "w") as f:
                f.write("ByeByeWorld")
            return True
        # Test from_step => to_step
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step="step5", inclusive=True),
                HammerStartStopStep(step="step5", inclusive=True)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_insertion_hook("step4", step5),
            hammer_vlsi.HammerTool.make_post_insertion_hook("step5", step6)
        ])
        assert success

        for i in range(1, 7):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i == 5:
                assert self.read(file) == "HelloWorld"
            else:
                assert not os.path.exists(file)

    def test_resume_pause_hooks_with_custom_steps2(self, test_context) -> None:
        def step5(x: hammer_vlsi.HammerTool) -> bool:
            with open(os.path.join(test_context.temp_dir, "step5.txt"), "w") as f:
                f.write("HelloWorld")
            return True

        def step6(x: hammer_vlsi.HammerTool) -> bool:
            with open(os.path.join(test_context.temp_dir, "step6.txt"), "w") as f:
                f.write("ByeByeWorld")
            return True
        # Test after_step => until_step
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step="step4", inclusive=False),
                HammerStartStopStep(step="step6", inclusive=False)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_insertion_hook("step4", step5),
            hammer_vlsi.HammerTool.make_post_insertion_hook("step5", step6)
        ])
        assert success

        for i in range(1, 7):
            file = os.path.join(test_context.temp_dir, "step{}.txt".format(i))
            if i == 5:
                assert self.read(file) == "HelloWorld"
            else:
                assert not os.path.exists(file)

    def test_persistent_hooks1(self, test_context) -> None:
        """Test that persistent hooks work."""

        # Test persist despite starting from step 3
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step="step3", inclusive=True),
                HammerStartStopStep(step=None, inclusive=False)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_persistent_hook(persist_hook(test_context.temp_dir))
        ])
        assert success
        file1 = os.path.join(test_context.temp_dir, "persist.txt")
        assert self.read(file1) == "HelloWorld"

    def test_persistent_hooks2(self, test_context) -> None:
        # Test pre_persist executes if anything before target step is run
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=None, inclusive=False),
                HammerStartStopStep(step="step2", inclusive=True)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_persistent_hook("step4", persist_hook(test_context.temp_dir))
        ])
        assert success
        file1 = os.path.join(test_context.temp_dir, "persist.txt")
        assert self.read(file1) == "HelloWorld"

    def test_persistent_hooks3(self, test_context) -> None:
        # Test pre_persist does not execute if starting from after target step
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step="step3", inclusive=True),
                HammerStartStopStep(step=None, inclusive=False)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_pre_persistent_hook("step2", persist_hook(test_context.temp_dir))
        ])
        assert success
        file1 = os.path.join(test_context.temp_dir, "persist.txt")
        assert not os.path.exists(file1)

    def test_persistent_hooks4(self, test_context) -> None:
        # Test post_persist does not execute if stopped before target step
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=None, inclusive=False),
                HammerStartStopStep(step="step2", inclusive=True)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_persistent_hook("step3", persist_hook(test_context.temp_dir))
        ])
        assert success
        file1 = os.path.join(test_context.temp_dir, "persist.txt")
        assert not os.path.exists(file1)

    def test_persistent_hooks5(self, test_context) -> None:
        # Test post_persist executes started after target step
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step="step3", inclusive=True),
                HammerStartStopStep(step=None, inclusive=False)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_persistent_hook("step1", persist_hook(test_context.temp_dir))
        ])
        assert success
        file1 = os.path.join(test_context.temp_dir, "persist.txt")
        assert self.read(file1) == "HelloWorld"

    def test_persistent_hooks6(self, test_context) -> None:
        # Test post_persist executes if target step is included in steps run
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step="step1", inclusive=True),
                HammerStartStopStep(step=None, inclusive=False)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_persistent_hook("step3", persist_hook(test_context.temp_dir))
        ])
        assert success
        file1 = os.path.join(test_context.temp_dir, "persist.txt")
        assert self.read(file1) == "HelloWorld"

    def test_persistent_hooks7(self, test_context) -> None:
        # Test replacement hook inherits replaced persistent hook behavior
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step="step3", inclusive=True),
                HammerStartStopStep(step=None, inclusive=False)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_persistent_hook("step1", persist_hook(test_context.temp_dir)),
            hammer_vlsi.HammerTool.make_replacement_hook("persist", persist_hook2(test_context.temp_dir))
        ])
        assert success
        file1 = os.path.join(test_context.temp_dir, "persist.txt")
        assert not os.path.exists(file1)
        file2 = os.path.join(test_context.temp_dir, "persist2.txt")
        assert self.read(file2) == "ByeByeWorld"

    def test_persistent_hooks8(self, test_context) -> None:
        # Test insertion hook inherits replaced persistent hook behavior
        test_context.driver.set_post_custom_syn_tool_hooks(
            hammer_vlsi.HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step="step3", inclusive=True),
                HammerStartStopStep(step=None, inclusive=False)
            )
        )
        success, syn_output = test_context.driver.run_synthesis(hook_actions=[
            hammer_vlsi.HammerTool.make_post_persistent_hook("step1", persist_hook(test_context.temp_dir)),
            hammer_vlsi.HammerTool.make_pre_insertion_hook("persist", persist_hook2(test_context.temp_dir))
        ])
        assert success
        file1 = os.path.join(test_context.temp_dir, "persist.txt")
        assert self.read(file1) == "HelloWorld"
        file2 = os.path.join(test_context.temp_dir, "persist2.txt")
        assert self.read(file2) == "ByeByeWorld"
