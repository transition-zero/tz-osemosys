<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/transition-zero/.github/raw/main/profile/img/logo-dark.png">
  <img alt="TransitionZero Logo" width="1000px" src="https://github.com/transition-zero/.github/raw/main/profile/img/logo-light.png">
  <a href="https://www.transitionzero.org/">
</picture>

# FEO-OSEMOSYS - a modern long-run systems modelling framework

<!-- Badges Begin -->

<!-- Badges End -->


**OSeMOSYS** is an open source modelling system for long-run systems analysis and planning.
It has been employed to develop energy systems models from the scale of the globe, continents, countries, regions, and villages.
OSeMOSYS is extremely flexible - it can be used for high-fidelity representations of power systems, rich with technological detail;
medium-fidelity representations of all-energy systems including upstream energy supply, final energy demand, and climate policities;
or low-fidelity nexus problems including commodities like materials, energy, and financing, and a range of environomental and social impacts.

OSeMOSYS is entirely open-source and can be used with a variety of programming languages and solvers.

## OSeMOSYS with the Future Energy Outlook

TransitionZero has rebuilt OSeMOSYS as a pip-installable Python package.
This implementation of OSeMOSYS underlies our Future Energy Outlook capacity expansion model builder.
We have added the following features:

* [Pydantic](https://docs.pydantic.dev/latest/)-based model construction and validation
* [Linopy](https://linopy.readthedocs.io/en/latest/)-based numerical optimsation and solving
* Reverse-compatability with [OSeMOSYS-otoole](https://github.com/OSeMOSYS/otoole)

## Documentation

FEO-OSeMOSYS

Quickstart

Examples

Future Energy Outlook

OSeMOSYS Docs

## Installation

FEO-OSeMOSYS can be installed with a simple `pip install feo-osemosys`. To solve a model, however, you'll need a solver. Any solver compatible with [Linopy](https://linopy.readthedocs.io/en/latest/) will work: [Coin-OR CBC](https://github.com/coin-or/Cbc), [GLPK](https://www.gnu.org/software/glpk/), [HiGHS](https://highs.dev/), [Gurobi](https://www.gurobi.com/solutions/gurobi-optimizer/), [CPLEX](https://dev.ampl.com/solvers/cplex/index.html), and more. We recommend HiGHS, the leading open-source solver.

### Solver Installation - HiGHS

HiGHS can be installed from source using `cmake` following the instructions [here](https://github.com/ERGO-Code/HiGHS?tab=readme-ov-file#installation). You'll need to install a cmake distribution for your relevant operating system.

*common issue: make sure you have write-privileges to default directory for `cmake --install build`, or either run this command with administrator privileges (`sudo cmake --install build` on mac and linux) or specify a different build directory*

### Docker installation

A docker container is provided that contains Python 3.11 and an installed version of HiGHS. You'll nedd to [install a docker distribution](https://docs.docker.com/engine/install/) relevant for your operating system.

The docker container is used in testing, but can also be used for local development work. The following docker command will run and enter the docker container, mount the current working directory at the `/home` directory, and change directory within the container to this directory.

    docker run -v $(pwd):/home -it  ghcr.io/transition-zero/tz-highs/highs-python:latest /bin/bash -c 'cd /home && /bin/bash'

*note! Any files changed within this mounted directory will persist, but any changes to environments, installed packes, etc. will not!*

## Quickstart

FEO-OSeMOSYS provides several entrypoints to get started quickly, however your model is specified.

**From Pydantic objects**

```python
from feo.osemosys import Model, Technology, TimeDefinition, Commodity, Region, OperatingMode

time_definition=TimeDefinition(id="years-only", years=range(2020,2051))
regions = [Region(id="single-region")]
commodities=[Commodity(id="electricity", demand_annual=25)]
impacts = []
technologies = [
    Technology(
        id="coal-gen",
        operating_life=40,
        capex=400,
        operating_modes=[
            OperatingMode(
                id="generation",
                opex_variable=5,
                output_activity_ratio={"electricity":1.}
            )
        ]
    )
]

model = Model(
    id="simple-carbon-price",
    time_definition=time_definition,
    regions=regions,
    commodities=commodities,
    impacts=impacts,
    technologies=technologies
)

model.solve()

```


**From Yaml/JSON**

```python
from feo.osemosys import load_model

my_model = load_model("path/to/yaml/directory")
```

**From Otoole outputs (legacy)**

```python
from feo.osemosys import Model

my_model = Model.from_otoole("path/to/otoole/csv/directory")
```

Read more in the [documentation]()

### Development

Create an environment of your choosing, for example with conda or venv. FEO-OSeMOSYS required Python=3.11.

In your environment, install FEO-OSeMOSYS in 'editable' mode and include the optional 'dev' dependencies.

    pip install -e ".[dev]"

Install the `pre-commit` hooks. Pre-commit does a bunch of useful things like delinting your code and catching missed imports.

    pre-commit install

#### Testing

Features must be associated with an appropriate test; tests must pass before being merged. Run tests using `pytest`.

    pytest

#### Pre-commit

On each commit, pre-commit will clean your commited files and raise any errors it finds.
You can ignore individual lines with the `# noqa` flag.
It is good practice to specify which error you'd like to ignore:

    <your line of code> # noqa: E123

You can run all the files in the repo at once using:

    pre-commit run --all-files

If you must, you can ignore pre-commit by using the `--no-verify` flag after your commit message:

    git commit -m "<your commit message>" --no-verify

Make sure you eventually delint any commits pushed this way or they will fail in CI/CD!
