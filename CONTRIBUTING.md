# Contributing

We welcome Pull Requests for general contributions. Please read the [code of conduct](CODE_OF_CONDUCT.md) before contributing. If you have a larger new feature or any questions on how to develop a fix, we recommend you open an [issue][issues] before starting. We recommend reading the [Goose docs on plugins](https://block-open-source.github.io/goose/plugins/plugins.html) for more information about how plugins work.

## Prerequisites

Goose uses [uv][uv] for dependency management, and formats with [ruff][ruff].
Make sure you have installed `uv` to install dependencies and run commands from within goose and the goose-plugins repositories.

## Getting Started

[Fork][fork] the repositories and clone to your local machine.

```sh
git clone https://github.com/block/goose
git clone https://github.com/block-open-source/goose-plugins
```

Create the virtual environment in each repository using `uv`.

```sh
uv sync
uv venv
```

Run the `source ... activate` command that is output by the `uv venv` command

### Install Goose Plugins to your local goose environment

Now that you have a local environment, you can install goose-plugins to your local environment in editable mode. This allows you to make changes to the plugins and see them reflected in your local goose. From within your goose repository, run the following command:

```
uv add --editable ~/path/to/goose-plugins
```

Run goose via `uv run` to iteratively develop your plugin

```sh
uv run goose session start
```

### Run Tests

To run the test suite against your edges, use `pytest`:

```sh
uv run pytest tests -m "not integration"
```

or use `just`

```sh
just test
```

## Opening a Pull Request

1. Create a new branch for your changes:

   ```sh
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure all tests pass:

   ```sh
   uv run pytest tests
   ```

3. Format your code using ruff:

   ```sh
   uv run ruff format .
   ```

4. Commit your changes following the [Conventional Commits](#conventional-commits) specification:

   ```sh
   git commit -m "feat: add new feature"
   ```

5. Push your changes to your fork:

   ```sh
   git push origin feature/your-feature-name
   ```

6. Visit the original repository on GitHub and click "New Pull Request"

7. Select your fork and the feature branch containing your changes

8. Fill out the pull request template with:

   - A clear title following Conventional Commits
   - A description of your changes
   - Any related issues
   - Testing steps
   - Screenshots (if applicable)

9. Submit the pull request and wait for review

10. Address any feedback or requested changes from maintainers

## Evaluations

Given that so much of Goose involves interactions with LLMs, our unit tests only go so far to confirming things work as intended.

We're currently developing a suite of evaluations, to make it easier to make improvements to Goose more confidently.

In the meantime, we typically incubate any new additions that change the behavior of the Goose through **opt-in** plugins - `Toolkit`s, `Moderator`s, and `Provider`s. We welcome contributions of plugins that add new capabilities to _goose_. We recommend sending in several examples of the new capabilities in action with your pull request.

Additions to the [developer toolkit][developer] change the core performance, and so will need to be measured carefully.

## Conventional Commits

This project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for PR titles. Conventional Commits make it easier to understand the history of a project and facilitate automation around versioning and changelog generation.

Common types include:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for adding or modifying tests
- `chore:` for routine tasks and maintenance

## Release

In order to release a new version of goose, you need to do the following:

1. Update version in `pyproject.toml` for `goose` and package dependencies such as `exchange`
2. Create a PR and merge it into main branch

This repo has a GitHub action that will automatically create a new release and publish the package to PyPI. These packages are not considered stable and are not recommended for production use.

[issues]: https://github.com/block/goose/issues
[goose-plugins]: https://github.com/block-open-source/goose-plugins
[ai-exchange]: https://github.com/block/goose/tree/main/packages/exchange
[developer]: https://github.com/block/goose/blob/dfecf829a83021b697bf2ecc1dbdd57d31727ddd/src/goose/toolkit/developer.py
[uv]: https://docs.astral.sh/uv/
[ruff]: https://docs.astral.sh/ruff/
[just]: https://github.com/casey/just
[adding-toolkit]: https://block.github.io/goose/configuration.html#adding-a-toolkit
[goose-docs]: https://block.github.io/goose/
[fork]: https://github.com/block/goose/fork
