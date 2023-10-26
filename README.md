# feo-osemosys
FEO OSeMOSYS - a TransitionZero implementation of OSeMOSYS to support the Future Energy Outlook

## Installation

FEO-OSeMOSYS can be installed with a simple `pip install`

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
