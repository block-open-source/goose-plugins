# Community plugins repository for [Goose][goose] 🧩 

<p align="center">
    <img src="docs/assets/goose_plugins_repository.png" alt="Goose Plugins Repository" width="500"/>
</p>


## 🎉 Hacktoberfest 2024 🎉

`goose-plugins` is a participating project in Hacktoberfest 2024! We’re so excited for your contributions, and have created a wide variety of issues so that anyone can contribute. Whether you're a seasoned developer or a first-time open source contributor, there's something for everyone.

### To get started:
1. Read the [contributing guide](https://github.com/square/goose-plugins/blob/main/CONTRIBUTING.md).
2. Read the [code of conduct](https://github.com/square/goose-plugins/blob/main/CODE_OF_CONDUCT.md).
3. Choose a task from this project's Hacktoberfest issues in [here](https://github.com/square/goose-plugins/issues) and follow the instructions. Each issue has the 🏷️ `hacktoberfest` label.

Have questions? Connecting with us in our [Discord community](https://discord.gg/DCAZKnGZFa) in the `#hacktoberfest` and `#goose-toolkits` project channel.

---

## Installation

```sh
pipx install goose-plugins --include-deps
```

To check that the plugins are installed, run

```sh
goose toolkit list
```

You should see the `artify` plugin in the list of available toolkits.

Then to run Goose, 

```sh
goose session start
```

## Developing Plugins

[Check out the Goose docs on plugins!](https://block-open-source.github.io/goose/index.html)

1. Clone the goose-plugins-exemplar repository and the goose repository
```sh
git clone https://github.com/block-open-source/goose
git clone https://github.com/block-open-source/goose-plugins
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
