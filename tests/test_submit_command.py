import json
import os
from typing import Dict, Any, List, Iterator
import importlib.resources as resources

from pydantic import BaseModel, validator
import pytest

from hammer import vlsi as hammer_vlsi
from hammer.config import HammerJSONEncoder
from hammer.logging import HammerVLSILogging
from hammer.utils import get_or_else


class SubmitCommandTestContext(BaseModel):
    echo_command_args: List[str] = ["go", "bears", "!"]
    echo_command: List[str] = ["echo", "go", "bears", "!"]
    logger = HammerVLSILogging.context("")
    env: Dict[Any, Any] = {}
    driver: hammer_vlsi.HammerDriver
    cmd_type: str
    submit_command: hammer_vlsi.HammerSubmitCommand
    temp_dir: str

    @validator("cmd_type")
    def cmd_type_validator(cls, cmd_type):
        if cmd_type not in ["lsf", "local"]:
            raise NotImplementedError("Have not built a test for %s yet" % cmd_type)

    class Config:
        arbitrary_types_allowed = True


@pytest.fixture()
def submit_command_test_context(tmp_path, cmd_type: str) -> Iterator[SubmitCommandTestContext]:
    """Initialize context by creating the temp_dir, driver, and loading mocksynth."""
    temp_dir = str(tmp_path)
    json_path = os.path.join(temp_dir, "project.json")
    json_content: Dict[str, Any] = {
        "vlsi.core.synthesis_tool": "hammer.synthesis.mocksynth",
        "vlsi.core.technology": "hammer.technology.nop",
        "synthesis.inputs.top_module": "dummy",
        "synthesis.inputs.input_files": ("/dev/null",),
        "synthesis.mocksynth.temp_folder": temp_dir,
        "synthesis.submit.command": cmd_type
    }
    if cmd_type is "lsf":
        assert resources.is_resource("utils", "mock_bsub.sh")
        with resources.path("utils", "mock_bsub.sh") as b:
            bsub_binary = str(b)
        json_content.update({
            "synthesis.submit.settings": [{"lsf": {
                "queue": "myqueue",
                "num_cpus": 4,
                "log_file": "test_log.log",
                "bsub_binary": bsub_binary,
                "extra_args": ("-R", "myresources")
            }}],
            "synthesis.submit.settings_meta": "lazyappend",
            "vlsi.submit.settings": [
                {"lsf": {"num_cpus": 8}}
            ],
            "vlsi.submit.settings_meta": "lazyappend"
        })

    with open(json_path, "w") as f:
        f.write(json.dumps(json_content, cls=HammerJSONEncoder, indent=4))

    options = hammer_vlsi.HammerDriverOptions(
        environment_configs=[],
        project_configs=[json_path],
        log_file=os.path.join(temp_dir, "log.txt"),
        obj_dir=temp_dir
    )
    driver = hammer_vlsi.HammerDriver(options)
    yield SubmitCommandTestContext(
        driver=driver,
        cmd_type=cmd_type,
        submit_command=hammer_vlsi.HammerSubmitCommand.get("synthesis", driver.database),
        temp_dir=temp_dir
    )


class TestSubmitCommand:
    @pytest.mark.parametrize("cmd_type", ["local"])
    def test_local_submit(self, submit_command_test_context) -> None:
        """ Test that a local submission produces the desired output """
        c = submit_command_test_context
        cmd = c.submit_command
        assert isinstance(cmd, hammer_vlsi.HammerLocalSubmitCommand)
        (output, returncode) = cmd.submit(c.echo_command, c.env, c.logger)

        assert output.splitlines()[0] == ' '.join(c.echo_command_args)
        assert returncode == 0

    @pytest.mark.parametrize("cmd_type", ["lsf"])
    def test_lsf_submit(self, submit_command_test_context) -> None:
        """ Test that an LSF submission produces the desired output """
        c = submit_command_test_context
        cmd = c.submit_command
        assert isinstance(cmd, hammer_vlsi.HammerLSFSubmitCommand)
        (raw_output, returncode) = cmd.submit(c.echo_command, c.env, c.logger)
        output = raw_output.splitlines()

        assert output[0] == "BLOCKING is: 1"
        assert output[1] == "QUEUE is: %s" % get_or_else(cmd.settings.queue, "")
        assert output[2] == "NUMCPU is: %d" % get_or_else(cmd.settings.num_cpus, 0)
        assert output[3] == "OUTPUT is: %s" % get_or_else(cmd.settings.log_file, "")

        extra = cmd.settings.extra_args
        has_resource = 0
        if "-R" in extra:
            has_resource = 1
            assert output[4] == "RESOURCE is: %s" % extra[extra.index("-R") + 1]
        else:
            raise NotImplementedError("You forgot to test the extra_args!")

        assert output[4 + has_resource], "COMMAND is: %s" % ' '.join(c.echo_command)
        assert output[5 + has_resource], ' '.join(c.echo_command_args)
        assert returncode == 0
