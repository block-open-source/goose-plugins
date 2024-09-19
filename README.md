# goose-plugins
Plugins for [Goose][goose]! 

## Installation

```sh
pipx install goose-plugins --include-deps
```

Then to run, 

```sh
goose session start
```

You should see listed the plugins that are available in the `goose-plugins` package.

## Developing Plugins

[Check out the Goose docs on plugins!][goose-docs]

1. Clone the goose-plugins-exemplar repository and the goose repository
```sh
git clone github.com/square/goose
git clone github.com/square/goose-plugins
```
2. Create the virtual environment for Goose in the Goose repo
```sh
uv sync
uv venv
```
Run the `source ... activate` command that is output by the `uv venv` command

3. Install the goose community plugins in editable mode
```sh
uv add --editable ~/path/to/goose-plugins
```
4. Run goose via `uv run` to iteratively develop your plugin
```sh
uv run goose session start
```

[goose]: https://github.com/square/goose
[goose-docs]: https://square.github.io/goose/plugins.html