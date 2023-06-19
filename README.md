[![Tests](https://github.com/DataShades/ckanext-editable-config/workflows/Tests/badge.svg?branch=main)](https://github.com/DataShades/ckanext-editable-config/actions)

# ckanext-editable-config

Edit CKAN configuration in runtime.

This plugin registers a set of API action for overriding config options and
applying the changes to application without restarting the web server.

**Note**: this plugin is not compatible with the CKAN's built-in AdminUI Config
form. Results are unpredictable when they are combined, so prefer to `Reset`
built-in config form and never use it if you going to rely on this plugin. Or,
at least, do not change the config option managed by AdminUI using the plugin's
API.

## Example

Change application's title:

```python
tk.get_action("editable_config_update")(
    {"ignore_auth": True},
    {
        "change": {
            "ckan.site_title": "Updated title"
        },
    },
)

```

## Requirements

Compatibility with core CKAN versions:

| CKAN version  | Compatible? |
|---------------|-------------|
| 2.9 and below | no          |
| 2.10          | yes         |
| master        | yes         |


## Installation

To install ckanext-editable-config:

1. Install the extension:
   ```sh
   pip install ckanext-editable-config
   ```

1. Add `editable_config` to the `ckan.plugins`.

## Usage

All the config options declared with the `editable: true` flag can be overriden
when the plugin is enabled. Every time the option is updated, it's new value
passed to the declared validators of the option. If any validator raises an
error, no changes happen. As long as option has proper validators configured,
it's safe to change its value.

There are 3 types of changes:

* `change`: option gets a new value.
* `revert`: option gets its previous value. For example, `ckan.site_title`
  intially has the value `CKAN`. Then you applied a `change` to it, setting
  title to `Updated title`. `revert` will set `ckan.site_title` back to
  `CKAN`. `revert` itself is a change, so double-revert doesn't change
  anything. It's not like `CTRL+Z`. Only the latest and one before the latest
  changes are kept.
* `reset`: remove all customizations from the config option and reset it to the
  state defined in the config file.

The only action you really need to remember is `editable_config_update`. It
accepts 3 collections:

* `change`: dictionary with option names and their new values
* `revert`: list of options that will be reverted
* `reset`: list of options that will be reset to the state of config file.

For example, if you want to change the value of the site title to `Updated
title`, revert site description to the previous value(whatever it was) and
reset all customizations of the About page, call the `editable_config_update`:
```python
tk.get_action("editable_config_update")(
    {"ignore_auth": True},
    {
        "change": {"ckan.site_title": "Updated title"},
        "revert": ["ckan.site_description"],
        "reset": ["ckan.site_about"],
    },
)
```

**Note**: all actions require sysadmin access.

## Config settings

```ini
# Additional options that can be changed via API even if they don't have
# `editable` flag enabled. Use it only when you are sure that changinging the
# option value won't break the application. For example, adding
# `ckan.datasets_per_page` here is relatively safe, because it is validated
# as an integer(but it's not 100% safe, because it's possible to assign
# negative number to this option and validators won't complain).
# (optional, default: )
ckanext.editable_config.options.extra_editable =
    ckan.datasets_per_page
    ckan.auth.user_create_groups

# Narrow down the list of editable config options. If this option is not
# empty, only `editable` options that are listed here can be changed via API.
# Attempt to change any other option, disregarding its `editable` flag, will
# cause a validation error.
# (optional, default: )
ckanext.editable_config.options.whitelist =
    ckan.site_title
    ckan.site_description

# Disable `editable` flag for the specified options. It's not possible to
# change the value of option mentioned here, even if it's `editable`.
# (optional, default: )
ckanext.editable_config.options.blacklist =
    ckan.site_title
    ckan.site_description
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
