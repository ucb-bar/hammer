import json
import os
from typing import Dict, Any, List, Iterator

from pydantic import BaseModel
import pytest

from hammer import vlsi as hammer_vlsi
from hammer.config import HammerJSONEncoder
from hammer.tech import ExtraLibrary, Library


class SRAMGeneratorTestContext(BaseModel):
    env: Dict[Any, Any] = {}
    driver: hammer_vlsi.HammerDriver
    temp_dir: str

    class Config:
        arbitrary_types_allowed = True


@pytest.fixture()
def sram_generator_test_context(tmp_path, tech: str) -> Iterator[SRAMGeneratorTestContext]:
    assert tech in {"nop", "asap7"}
    temp_dir = str(tmp_path)
    json_path = os.path.join(temp_dir, "project.json")
    json_content: Dict[str, Any] = {
        "vlsi.core.technology": "hammer.technology.nop", # can't load asap7 because we don't have the tarball
        "vlsi.core.sram_generator_tool": "hammer.sram_generator.mocksram_generator",
        "sram_generator.inputs.top_module": "dummy",
        "sram_generator.inputs.layout_file": "/dev/null",
        "sram_generator.temp_folder": temp_dir,
        "sram_generator.submit.command": "local"
    }
    if tech == "nop":
        json_content.update({
            "vlsi.inputs.sram_parameters": [{"depth": 32, "width": 32,
                                             "name": "small", "family": "1r1w", "mask": False, "vt": "SVT", "mux": 1},
                                            {"depth": 64, "width": 128,
                                             "name": "large", "family": "1rw", "mask": True, "vt": "SVT", "mux": 2}],
            "vlsi.inputs.mmmc_corners": [{"name": "c1", "type": "setup", "voltage": "0.5V", "temp": "0C"},
                                         {"name": "c2", "type": "hold", "voltage": "1.5V", "temp": "125C"}]
        })
    else:  # asap7
        json_content.update({
            "vlsi.inputs.sram_parameters": [{"depth": 32, "width": 32,
                                             "name": "small", "family": "2RW", "mask": False, "vt": "SRAM", "mux": 1},
                                            {"depth": 64, "width": 128,
                                             "name": "large", "family": "1RW", "mask": False, "vt": "SRAM", "mux": 1}],
            "vlsi.inputs.mmmc_corners": [{"name": "PVT_0P63V_100C", "type": "setup", "voltage": "0.63V", "temp": "100C"},
                                         {"name": "PVT_0P77V_0C", "type": "hold", "voltage": "0.77V", "temp": "0C"}]
        })
        json_content.update({
            "vlsi.core.sram_generator_tool": "hammer.technology.asap7.sram_compiler"
        })

    with open(json_path, "w") as f:
        f.write(json.dumps(json_content, cls=HammerJSONEncoder, indent=4))

    options = hammer_vlsi.HammerDriverOptions(
        environment_configs=[],
        project_configs=[json_path],
        log_file=os.path.join(temp_dir, "log.txt"),
        obj_dir=temp_dir
    )
    yield SRAMGeneratorTestContext(driver=hammer_vlsi.HammerDriver(options), temp_dir=temp_dir)


class TestHammerSRAMGenerator:
    @pytest.mark.parametrize("tech", ["nop"])
    def test_get_results(self, sram_generator_test_context) -> None:
        """ Test that multiple srams and multiple corners have their
            cross-product generated."""
        c = sram_generator_test_context
        assert c.driver.load_sram_generator_tool()
        assert c.driver.run_sram_generator()
        assert isinstance(c.driver.sram_generator_tool, hammer_vlsi.HammerSRAMGeneratorTool)
        output_libs = c.driver.sram_generator_tool.output_libraries # type: List[ExtraLibrary]
        assert isinstance(output_libs, list)
        # Should have an SRAM for each corner(2) and parameter(2) for a total of 4
        assert len(output_libs) == 4
        libs: List[Library] = list(map(lambda ex: ex.library, output_libs))
        gds_names: List[str] = [lib.gds_file for lib in libs if lib.gds_file is not None]
        assert set(gds_names), {"sram32x32_0.5V_0.0C.gds", "sram32x32_1.5V_125.0C.gds", "sram64x128_0.5V_0.0C.gds",
                                "sram64x128_1.5V_125.0C.gds"}

    @pytest.mark.parametrize("tech", ["asap7"])
    def test_get_results_asap7(self, sram_generator_test_context) -> None:
        """ Test that multiple srams and multiple corners have their
            cross-product generated."""
        c = sram_generator_test_context
        assert c.driver.load_sram_generator_tool()
        assert c.driver.run_sram_generator()
        assert isinstance(c.driver.sram_generator_tool, hammer_vlsi.HammerSRAMGeneratorTool)
        output_libs = c.driver.sram_generator_tool.output_libraries # type: List[ExtraLibrary]
        print(output_libs)
        assert isinstance(output_libs, list)
        # Should have an SRAM for each corner(2) and parameter(2) for a total of 4
        assert len(output_libs) == 4
        libs: List[Library] = list(map(lambda ex: ex.library, output_libs))
        verilog_names: List[str] = [lib.verilog_sim for lib in libs if lib.verilog_sim is not None]
        assert set(verilog_names) == {os.path.join(c.temp_dir, "tech-nop-cache", "SRAM2RW32x32.v"),
                                      os.path.join(c.temp_dir, "tech-nop-cache", "SRAM1RW64x128.v")}
