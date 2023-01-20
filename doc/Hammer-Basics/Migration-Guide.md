# Migration Guide

Hammer's software infrastructure changed significantly for version 1.0.0. In order to use the latest version of Hammer, you will need to make changes to your existing tool/tech plugins, YML/JSON input files, and Python files that import Hammer.

This guide is relevant for both plugin developers and general users.

[The documentation for old Hammer is cached here](https://hammer-vlsi.readthedocs.io/en/0.1.0/).

## `import` Statements

When importing Hammer classes and/or methods, replace old statements:

```python3
import hammer_tech
from hammer_vlsi import HammerTool
```

with:

```python3
import hammer.tech
from hammer.vlsi import HammerTool
```

The rule of thumb is that underscores are replaced with periods. This will match the package directory structure under the `hammer/` directory.

## Technology JSON

Previously, the technology JSON file may have contained entries like this:

```json
"gds map file": "path/to/layermap.file"
```

Now, keys must not contain spaces in line with JSON syntax:

```json
"gds_map_file": "path/to/layermap.file"
```

The fields for `installs` and `tarballs` have also changed. Generally, `path` is now `id` and `base var` is now `path` to remove confusion.
For example, previously (ASAP7 example for reference):

```json
"installs": [
  {
    "path": "$PDK",
    "base var": "technology.asap7.pdk_install_dir"
  }
],
"tarballs": [
  {
    "path": "ASAP7_PDK_CalibreDeck.tar",
    "homepage": "http://asap.asu.edu/asap/",
    "base var": "technology.asap7.tarball_dir"
  }
]
```

is now:
```json
"installs": [
  {
    "id": "$PDK",
    "path": "technology.asap7.pdk_install_dir"
  }
],
"tarballs": [
  {
    "root": {
      "id": "ASAP7_PDK_CalibreDeck.tar",
      "path": "technology.asap7.tarball_dir"
    },
    "homepage": "http://asap.asu.edu/asap/",
    "optional": true
  }
]
```

## Plugin File Structure

Plugins previously did not have a file structure requirement. For example, it could have looked like this:

```
mytech/
    __init__.py
    defaults.yml
    mytech.tech.json
    layer.map         # some tech-specific file
action/
    action_tool/
        __init__.py   # contains action_tool-specific hooks
        tool.options  # some tech-specific file needed by this tool
```

The new structure must follow Python package convention, hence it will look as follows:

```
hammer/
    mytech/
        __init__.py
        defaults.yml
        mytech.tech.json
        layer.map         # some tech-specific file
        action/
            action_tool/
                __init__.py   # contains action_tool-specific hooks
                tool.options  # some tech-specific file needed for this tool
```

## Resource Files

Technology plugins will often provide special static files needed by tools, such as the `layer.map` file in the above example. If this file is already specified with the `prependlocal` meta action, the behavior will remain the same:

```yaml
action.tool.layer_map: "layer.map"
action.tool.layer_map_meta: prependlocal
```

However, within a plugin, if you need to access to a specific file for a tool-specific hook, for example, in `action/action_tool/__init__.py`, replace this:

```python
with open(os.path.join(self.tool_dir, "tool.options")) as f:
```

With this and append `Pathlib` methods like `read_text()` as required:

```python
importlib.resources.files(self.package).joinpath("tool.options")
```

## `pyproject.toml`

Plugins that are repositories separate from Hammer must now have a `pyproject.toml` file so that they become poetry projects. Refer to [](poetry_project) for details. 
