# Community plugins repository for [Goose][goose] 🧩

<p align="center">
  <img src="docs/assets/goose_plugins_repository.png" alt="Goose Plugins Repository" width="500"/>
</p>

## 🪿 Loose Goose November 2024 🪿

`goose-plugins` is participating in Loose Goose November 2024! 🪿 We’re so excited for your contributions, and have created a wide variety of content issues so that anyone can contribute. Whether you're a seasoned developer or a first-time open source contributor, there's something for everyone. 

### This event is open to both Block employees and external contributors! 🦢

### To get started:

1. Read the [contributing guide](https://github.com/square/goose-plugins/blob/main/CONTRIBUTING.md).
2. Read the [code of conduct](https://github.com/square/goose-plugins/blob/main/CODE_OF_CONDUCT.md).
3. Choose a task from our Loose Goose Project Hub [here](https://github.com/block-open-source/goose-plugins/issues/32) and follow the instructions. Each issue has the 🏷️ `loosegoose` label.

Have questions? Connecting with us in our [Discord community](https://discord.gg/DCAZKnGZFa) in the `#loosegoose` and `#goose-toolkits` project channel.

---

## Installation

Goose plugins are currently only available by cloning this repository and linking to your local version of Goose. Installation via a package manager is being investigated. Keep an eye out for updates!

These instructions assume have cloned the Goose repository and the Goose plugins repository and are able to run goose running via `uv run goose`.

1. List the current toolkits available

```sh
uv run goose toolkit list
```

2. Install the goose community plugins in editable mode

```sh
uv add --editable ~/path/to/goose-plugins
```

3. List the toolkits again to see the new plugins

```sh
uv run goose toolkit list
```

You should see the community plugins in the list of available toolkits.

4. Add the plugin to your Goose configuration file

Update your config at `~/.config/goose/profile.yaml` to include the plugin you want to use.

```yaml
default:
  provider: anthropic
  processor: claude-3-5-sonnet-20240620
  accelerator: claude-3-5-sonnet-20240620
  moderator: truncate
  toolkits:
    - name: developer
      requires: {}
    - name: your_community_plugin
      requires: {}
```

5. Start a new goose session and your plugin should be available.

```sh
uv run goose session start
```

## Developing Plugins

Check out the [Goose docs on plugins!](https://block.github.io/goose/plugins/plugins.html) for more information on developing plugins.

1. [Fork][fork] the repositories and clone to your local machine.

```sh
git clone https://github.com/block/goose
git clone https://github.com/block-open-source/goose-plugins
```

2. Create the virtual environment in each repository using `uv`.

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
[fork]: https://github.com/block-open-source/goose-plugins/fork
