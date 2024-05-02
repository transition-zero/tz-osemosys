<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/transition-zero/.github/raw/main/profile/img/logo-dark.png">
  <img alt="TransitionZero Logo" width="1000px" src="https://github.com/transition-zero/.github/raw/main/profile/img/logo-light.png">
  <a href="https://www.transitionzero.org/">
</picture>

# TZ-OSEMOSYS - a modern long-run systems modelling framework

<!-- badges-begin -->

[![License][license badge]][license]
[![Contributor Covenant][contributor covenant badge]][code of conduct]
![Tests][tests badge]
![Coverage][coverage badge]
![Python][python badge]
![Status][status badge]

[license badge]: https://img.shields.io/github/license/ad-aures/castopod?color=blue
[license]: https://opensource.org/license/agpl-v3

[contributor covenant badge]: https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg
[code of conduct]: https://github.com/transition-zero/tz-osemosys/blob/main/CODE-OF-CONDUCT.md

[tests badge]: https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Lkruitwagen/feffb38d46c750cad5402dca5dd54bf9/raw/tests_passing.json

[coverage badge]: https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Lkruitwagen/6afead97828812b3c9ad498c94dd45f8/raw/coverage_badge.json

[python badge]: https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Lkruitwagen/bd1e357c1bce5fc2c0808bcdb569157c/raw/python_version_badge.json

[status badge]: https://img.shields.io/badge/under%20construction-ffae00

<!-- badges-end -->


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

[TZ-OSeMOSYS](https://docs.feo.transitionzero.org/)

[Examples](examples)

[TransitionZero Platform Docs](https://docs.feo.transitionzero.org/)

[OSeMOSYS Docs](https://osemosys.readthedocs.io/en/latest/)

## Installation

TZ-OSeMOSYS can be installed with a simple `pip install tz-osemosys`. To solve a model, however, you'll need a solver. Any solver compatible with [Linopy](https://linopy.readthedocs.io/en/latest/) will work: [Coin-OR CBC](https://github.com/coin-or/Cbc), [GLPK](https://www.gnu.org/software/glpk/), [HiGHS](https://highs.dev/), [Gurobi](https://www.gurobi.com/solutions/gurobi-optimizer/), [CPLEX](https://dev.ampl.com/solvers/cplex/index.html), and more. We recommend HiGHS, the leading open-source solver.

### Solver Installation - HiGHS

HiGHS can be installed from source using `cmake` following the instructions [here](https://github.com/ERGO-Code/HiGHS?tab=readme-ov-file#installation). You'll need to install a cmake distribution for your relevant operating system.

*common issue: make sure you have write-privileges to default directory for `cmake --install build`, or either run this command with administrator privileges (`sudo cmake --install build` on mac and linux) or specify a different build directory*

### Docker installation

A docker container is provided that contains Python 3.11 and an installed version of HiGHS. You'll need to [install a docker distribution](https://docs.docker.com/engine/install/) relevant for your operating system.

The docker container is used in testing, but can also be used for local development work. The following docker command will run and enter the docker container, mount the current working directory at the `/home` directory, and change directory within the container to this directory.

```console
docker run -v $(pwd):/home -it  ghcr.io/transition-zero/tz-highs/highs-python:latest /bin/bash -c 'cd /home && /bin/bash'
```

*note! Any files changed within this mounted directory will persist, but any changes to environments, installed packes, etc. will not!*

## Quickstart

TZ-OSeMOSYS provides several entrypoints to get started quickly, however your model is specified.

### From Pydantic objects

Models can be specified directly with Pydantic objects. Pydantic gives useful tooling for class inheritance and field validation. The Model class and subclasses provide obvious semantic linking between the object types. The set of objects comprising the model is mutually exclusive - no information is repeated - and collectively exhaustive - no information needs to be extracted from csvs or other data sources.

```python
from tz.osemosys import (
    Model,
    Technology,
    TimeDefinition,
    Commodity,
    Region,
    Impact,
    OperatingMode,
)

time_definition = TimeDefinition(id="years-only", years=range(2020, 2051))
regions = [Region(id="single-region")]
commodities = [Commodity(id="electricity", demand_annual=25 * 8760)]  # 25GW * 8760hr/yr
impacts = [Impact(id="CO2", penalty=60)]  # 60 $mn/Mtonne
technologies = [
    Technology(
        id="coal-gen",
        operating_life=40,  # years
        capex=800,  # mn$/GW
        # straight-line reduction to 2040
        residual_capacity={
            yr: 25 * max((1 - (yr - 2020) / (2040 - 2020), 0))
            for yr in range(2020, 2051)
        },
        operating_modes=[
            OperatingMode(
                id="generation",
                # $mn20/Mt.coal / 8.14 TWh/Mt coal * 8760 GWh/GW / 0.3 /1000 GWh/TWh (therm eff)
                opex_variable=20 / 8.14 * 8760 / 0.3 / 1000,  # $71/GW/yr
                output_activity_ratio={"electricity": 1.0 * 8760},  # GWh/yr/GW
                emission_activity_ratio={
                    "CO2": 0.354 * 8760 / 1000
                },  # Mtco2/TWh * 8760GWh/Gw/yr /1000 GWh/TWh
            )
        ],
    ),
    Technology(
        id="solar-pv",
        operating_life=25,
        capex=1200,
        capacity_factor=0.3,
        operating_modes=[
            OperatingMode(
                id="generation",
                opex_variable=0,
                output_activity_ratio={"electricity": 1.0 * 8760},  # GWh/yr/GW
            )
        ],
    ),
]

model = Model(
    id="simple-carbon-price",
    time_definition=time_definition,
    regions=regions,
    commodities=commodities,
    impacts=impacts,
    technologies=technologies,
)

model.solve()
```


### From Yaml

YAML is a human-readable data serialisation language. We've build a custom YAML parser that allows the creation of model configurations that are _exhaustive_ while also being _expressive_.

- model fields can be cross-referenced in the yaml blob, e.g. `my_field: ${commodities[0].COAL.demand}`.
- model fields can also be populated from environment variables: `my_field: $ENV{MYVAR}`.
- simple Python expressions are automatically evaluated, including list comprehensions, dictionary comprehensions, `min`, `max`, `sum`, and `range` functions.
- for data keyed by an osemosys `set` (e.g. `YEARS`, `TIMESLICES`, `TECHNOLOGIES`), wildcards `"*"` can be used in place of explicitly listing all set members.
- data field `set` dimensions and membership are also automatically inferred - a single value can be given which will be broadcast to all set member combinations.
- single or multiple `.yaml` files can be composed together, allowing you to separate, e.g. `technologies.yaml`, from the rest of your model.

```python
from tz.osemosys import Model

my_model = Model.from_yaml("path/to/yaml/directory")
```

### From Otoole outputs (legacy)

TZ-OSeMOSYS is provided with backwards compatability with the [otoole](https://github.com/OSeMOSYS/otoole) osemosys tooling. Any legacy models can be loaded from the directory of otoole-formatted csvs.

```python
from tz.osemosys import Model

my_model = Model.from_otoole_csv("path/to/otoole/csv/directory")
```

Read more in the [documentation](https://docs.feo.transitionzero.org/)

### Development and Contributing

We welcome contributions! To get started as a contributor or as a developer, please read our [contributor guidelines](./CONTRIBUTING.md).
