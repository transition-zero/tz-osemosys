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

FEO-OSeMOSYS can be installed with a simple `pip install feo-osemosys`.

## Quickstart

FEO-OSeMOSYS provides several entrypoints to get started quickly, however your model is specified.

**From Pydantic objects**

```
from feo.osemosys import TimeDefinition, Region, Technology, Commodity, Impact, Model

...
```


**From Yaml/JSON**

```
from feo.osemosys import load_model

my_model = load_model("path/to/yaml/directory")
```

**From Otoole outputs (legacy)**

```
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
