# Hammer Setup

Hammer depends on Python 3.9+.

The Hammer setup is different based on its usecase, which are summarized as follows:

* [User Setup](#user-setup): Use Hammer with no modifications.
* [Power User Setup](#power-user-setup): Modify Hammer and see these changes immediately reflected when calling Hammer [recommended].
* [Developer Setup](#developer-setup): Developing major Hammer features, adding dependencies, running Hammer unit tests, etc.

Note that some tools and technologies have extra setup requirements:
* [ASAP7 setup directions](https://github.com/ucb-bar/hammer/blob/master/hammer/technology/asap7/README.md)
* [Sky130 & OpenROAD tools setup](https://hammer-vlsi.readthedocs.io/en/stable/Examples/openroad-sky130.html)

## User Setup

Install the hammer python package from PyPI.

```shell
pip install hammer-vlsi

# if using the ASAP7 PDK you need the gdspy or gdstk dependencies
pip install hammer-vlsi[asap7]        # default: gdspy
pip install hammer-vlsi[asap7-gdstk]  # install gdstk instead

# verify that you can run the `hammer-vlsi` script from the command line
hammer-vlsi -h
```

## Power User Setup
Install Hammer as a source dependency to some target virtual environment, such as conda.

```shell
# clone Hammer somewhere on your disk
git clone https://github.com/ucb-bar/hammer.git

# activate your target virtual environment, e.g. Chipyard
#   commands vary for this based on your package/environment manager:
#     conda activate <env name>
#     source <path>/.venv/bin/activate

# install hammer package in editable mode to your environment
cd hammer
pip install -e .  # run this after activating your target environment

```

### Installing from Another Poetry Project

Hammer tool (e.g. `hammer-cadence-plugins`) and PDK plugin repositories are poetry projects (with a `pyproject.toml` in their root).
To depend on Hammer as a source dependency, first clone Hammer somewhere on your disk.
Then add this snippet to the tool/PDK plugin repo's `pyproject.toml` (and remove any PyPI dependency on Hammer):

```toml
[tool.poetry.dependencies]
#hammer-vlsi = "^1.0.0"
hammer-vlsi = {path = "path/to/hammer", extras = ["asap7"], develop = true}
```

Run `poetry update` and `poetry install`.
Do not commit the changes to `pyproject.toml` or `poetry.lock` without first removing the source dependency.
You only need to specify `extras` if you need the `asap7` optional dependency (gdstk).


## Developer Setup

1. Clone Hammer with `git`

```shell
git clone git@github.com:ucb-bar/hammer
cd hammer
```
2. [Install poetry](https://python-poetry.org/docs/master/) to manage the development virtualenv and dependencies

```shell
curl -sSL https://install.python-poetry.org | python3 -
```

3. Create a poetry-managed virtualenv using the dependencies from `pyproject.toml`

```shell
# create the virtualenv inside the project folder (in .venv)
poetry config virtualenvs.in-project true
poetry install
```

4. Activate the virtualenv. Within the virtualenv, Hammer is installed and you can access its scripts defined in
    `pyproject.toml` (in `[tool.poetry.scripts]`)

```shell
poetry shell
hammer-vlsi -h
```

### Using PyCharm

This project works out of the box with PyCharm.
You should install the [Pydantic plugin](https://plugins.jetbrains.com/plugin/12861-pydantic) to enable autocomplete for Pydantic BaseModels.

### Unit Tests with pytest

Within the poetry virtualenv, from the root of Hammer, run the tests (`-v` will print out each test name explicitly)

```shell
pytest tests/ -v
```

If you want to skip the single long running-test in `test_stackup.py`:

```shell
pytest tests/ -m "not long" -v
```

If you want to run only a specific test use `-k` with a snippet of the test function you want to run:

```shell
pytest tests/ -k "lsf" -v

> tests/test_submit_command.py::TestSubmitCommand::test_lsf_submit[lsf] PASSED
```

By default, `pytest` will only display what a test prints to stdout if the test fails.
To display stdout even for a passing test, use `-rA`:

```shell
pytest tests/test_build_systems.py -k "flat_makefile" -rA -v

> __________________ TestHammerBuildSystems.test_flat_makefile _________________
> ---------------------------- Captured stdout call ----------------------------
> [<global>] Loading hammer-vlsi libraries and reading settings
> [<global>] Loading technology 'nop'
> =========================== short test summary info ==========================
> PASSED tests/test_build_systems.py::TestHammerBuildSystems::test_flat_makefile
```

### Type Checking with pyright

Run: `poetry run pyright`

### Testing Different Python Versions with tox

Hammer is supposed to work with Python 3.9+, so we run its unit tests on all supported Python versions using `tox` and `pyenv`.

1. [Install `pyenv`](https://github.com/pyenv/pyenv-installer)

```shell
curl https://pyenv.run | bash
```

Restart your shell and run `pyenv init` (and follow any of its instructions).
Then restart your shell again.

2. Install Python versions

See the `.python-version` file at the root of hammer and install those Python versions using `pyenv`.

```shell
pyenv install 3.9.13
pyenv install 3.10.6
```

Once the Python interpreters are installed, run `pyenv versions` from the root of hammer.

```shell
pyenv versions
  system
* 3.9.13 (set by .../hammer/.python-version)
* 3.10.6 (set by .../hammer/.python-version)
```

3. From within your `poetry` virtualenv, run `tox`

```shell
tox
```

This will run the pytest unit tests using all the Python versions specified in `pyproject.toml` under the `[tool.tox]` key.

You can run tests only on a particular environment with `-e`

```shell
tox -e py39 # only run tests on Python 3.9
```

You can pass command line arguments to the pytest invocation within a tox virtualenv with `--`

```shell
tox -e py39 -- -k "lsf" -v
```

### Adding / Updating Dependencies

To add a new Python (`pip`) dependency, modify `pyproject.toml`.
If the dependency is only used for development, add it under the key `[tool.poetry.dev-dependencies]`, otherwise add it under the key `[tool.poetry.dependencies]`.
Then run `poetry update` and `poetry install`.
The updated `poetry.lock` file should be committed to Hammer.

To update an existing dependency, modify `pyproject.toml` with the new version constraint.
Run `poetry update` and `poetry install` and commit `poetry.lock`.

### Building Documentation

First, generate the `schema.json` file from within your poetry virtualenv:

```shell
python3 -c "from hammer.tech import TechJSON; print(TechJSON.schema_json(indent=2))" > doc/Technology/schema.json
```

Then:
- `cd doc`
- Modify any documentation files. You can migrate any rst file to Markdown if desired.
- Run `sphinx-build . build`
- The generated HTML files are placed in `build/`
- Open them in your browser `firefox build/index.html`

### Publishing

Build a sdist and wheel (results are in `dist`):

```shell
poetry build
```

To publish on TestPyPI:

1. Create an account on [TestPyPi](https://test.pypi.org/)
2. Note the source repository `testpypi` in `pyproject.toml` under the key `[tool.poetry.source]`
   - To add another [PyPI repository to poetry](https://python-poetry.org/docs/master/repositories/): `poetry source add <source name> <source url>`
3. Publish: `poetry publish --repository testpypi -u <username> -p <password>`
