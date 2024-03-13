# Development and Contributing

All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.

If you are simply looking to start working with the codebase, navigate to the GitHub "issues" tab and start looking through interesting issues. There are a number of issues listed under Docs and good first issue where you could start out.

Feel free to ask questions on the mailing list or on Slack.

As contributors and maintainers to this project, you are expected to abide by TransitionZero's code of conduct. More information can be found in the [Code of Conduct](./CODE-OF-CONDUCT.md).


Create an environment of your choosing, for example with conda or venv. TZ-OSeMOSYS required Python=3.11.

In your environment, install TZ-OSeMOSYS in 'editable' mode and include the optional 'dev' dependencies.

```console
pip install -e ".[dev]"
``````

Install the `pre-commit` hooks. Pre-commit does a bunch of useful things like delinting your code and catching missed imports.

```console
pre-commit install
```

#### Testing

Features must be associated with an appropriate test; tests must pass before being merged. Run tests using `pytest`.

```console
pytest
```

#### Pre-commit

On each commit, pre-commit will clean your commited files and raise any errors it finds.
You can ignore individual lines with the `# noqa` flag.
It is good practice to specify which error you'd like to ignore:

```console
<your line of code> # noqa: E123
```

You can run all the files in the repo at once using:

```console
pre-commit run --all-files
```

If you must, you can ignore pre-commit by using the `--no-verify` flag after your commit message:

```console
git commit -m "<your commit message>" --no-verify
```

Make sure you eventually delint any commits pushed this way or they will fail in CI/CD!
