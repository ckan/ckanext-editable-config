[![Tests](https://github.com/DataShades/ckanext-editable-config/workflows/Tests/badge.svg?branch=main)](https://github.com/DataShades/ckanext-editable-config/actions)

# ckanext-editable-config

Edit CKAN configuration in runtime.

This plugin registers a set of API action for overriding config options and
applying the changes to application without restarting the web server.

## Example

Change application's title:

* from Python:
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

* from CLI:
  ```sh
  ckanapi action editable_config_update change:'{"ckan.site_title": "Updated via ckanapi"}'
  ```

* from browser:
  ```javascript
  await fetch("/api/action/editable_config_update", {
    method: "POST",
    body: JSON.stringify({change: {"ckan.site_title": "Updated from JS"}}),
    headers: {"content-type": "application/json"},
  })
  ```

## Content

* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
* [Config settings](#config-settings)
* [API actions](#api-actions)
* [Troubleshooting](#troubleshooting)

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
  anything. It's not like `CTRL+Z`, rather it just swaps current and previous
  values. Only the latest and one before the latest changes are kept.
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

Check [API actions](#api-actions) and [troubleshooting](#troubleshooting)
sections below if you need something more sophisticated.

## Config settings

```ini

# Additional options that can be changed via API even if they don't have
# `editable` flag enabled. Use it only when you are sure that changinging the
# option value won't break the application. For example, adding
# `ckan.datasets_per_page` here is relatively safe, because it is validated
# as an integer(but it's not 100% safe, because it's possible to assign
# negative number to this option and validators won't complain).
# (optional, default: )
ckanext.editable_config.options.extra_editable = ckan.datasets_per_page ckan.auth.user_create_groups

# Narrow down the list of editable config options. If this option is not
# empty, only `editable` options that are listed here can be changed via API.
# Attempt to change any other option, disregarding its `editable` flag, will
# cause a validation error.
# (optional, default: )
ckanext.editable_config.options.whitelist = ckan.site_title ckan.site_description

# Disable `editable` flag for the specified options. It's not possible to
# change the value of option mentioned here, even if it's `editable`.
# (optional, default: )
ckanext.editable_config.options.blacklist = ckan.site_title ckan.site_description

# Minimal number of seconds between two consequent change detection cycles.
# Basically, if you set 60 as a value, plugin will check config chnages once
# in a minute. In this way you can reduce number of DB queries and avoid
# unnecesarry checks when static files are served by CKAN.  Note, these
# queries are pretty fast(1ms), so you won't notice any significant
# performance improvement by setting any non-zero value here. And it means
# that any config overrides applied by API actions may not be visible
# immediately - you'll have to wait `charge_timeout` seconds in worst case.
# (optional, default: 0)
ckanext.editable_config.charge_timeout = 10

# Additional validators that are used when config option overrides are
# applied. Use this option if CKAN validators are not strict enough and you
# see the way to break the application by providing valid values for options.
# (optional, default: {})
ckanext.editable_config.additional_validators = {"ckan.site_title": "less_than_100 do_not_contain_exclamation_mark"}

# Remove "Config" tab from CKAN's Admin UI.
# (optional, default: false)
ckanext.editable_config.disable_admin_config_tab = True

# Replace "Config" tab from CKAN's Admin UI with basic form for editable
# config options.
# (optional, default: false)
ckanext.editable_config.replace_admin_config_tab = True

# Automatically convert any existing config overrides added via CKAN's Admin
# UI into editable config overrides.
# (optional, default: false)
ckanext.editable_config.convert_core_overrides = True

```

## API actions

### `editable_config_last_check`

Date and time of the last change detection cycle.

Returns:
* `last_check`(`str`): ISO datetime

Example:
```sh
$ ckanapi action editable_config_last_check
{
  "last_check": "2023-07-26T08:24:48.013121"
}

```
### `editable_config_list`

All editable config options. Every modified option includes dictionary
containing override details.

Returns:
* editable options(`dict[str, Any]`): key: option name; value: dictionary with
  current value and optional modification details

Example:
```sh
$ ckanapi action editable_config_list
{
  "ckan.site_about": {
    "option": null,
    "value": ""
  },
  "ckan.site_title": {
    "option": {
      "key": "ckan.site_title",
      "prev_value": "CKAN",
      "updated_at": "2023-07-25T21:44:52.434211",
      "value": "Updated title"
    },
    "value": "Updated title"
  }
}

```

### `editable_config_change`

Change multiple config options using `options` mapping with pairs of options
name and option value.

Returns:
* updated options(`dict[str, Any]`): key: option name; value: dictionary
  with updated option details

Example:
```sh
$ ckanapi action editable_config_change options='{"ckan.site_title": "Updated"}'
{
  "ckan.site_title": {
    "key": "ckan.site_title",
    "prev_value": "CKAN",
    "updated_at": "2023-07-26T08:28:04.988247",
    "value": "Updated"
  }
}

```

### `editable_config_revert`

Swap current and previous value of the option using `keys` list of option names.

Returns:
* updated options(`dict[str, Any]`): key: option name; value: dictionary with
  option details after revert

Example:
```sh
$ ckanapi action editable_config_revert keys=ckan.site_title
{
  "ckan.site_title": {
    "key": "ckan.site_title",
    "prev_value": "Updated",
    "updated_at": "2023-07-26T08:28:59.667917",
    "value": "CKAN"
  }
}
```

### `editable_config_reset`

Remove optio modifications using `keys` list of option names.

Returns:
* removed options(`dict[str, Any]`): key: option name; value: dictionary with
  removed option details

Example:
```sh
$ ckanapi action editable_config_reset keys=ckan.site_title
{
  "ckan.site_title": {
    "key": "ckan.site_title",
    "prev_value": "Updated",
    "updated_at": "2023-07-26T08:28:59.667917",
    "value": "CKAN"
  }
}

```

### `editable_config_update`

Combine `change`, `revert` and `reset` actions into a single action. Accepts
`change` dictionary, `revert` list, and `reset` list. Swiss-knife that exists
merely for bulk operations.

Returns:
* updated option(`dict[str, Any]`): key: option name; value: dictionary
  with current value and optional modification details

Example
```sh
$ ckanapi action editable_config_update \
$    change='{"ckan.site_about": "Updated via ckanapi"}' \
$    revert=ckan.site_title \
$    reset=ckan.site_custom_css
{
  "change": {
    "ckan.site_about": {
      "key": "ckan.site_about",
      "prev_value": "Updated via ckanapi",
      "updated_at": "2023-07-26T08:35:25.462359",
      "value": "Updated via ckanapi"
    }
  },
  "reset": {
    "ckan.site_custom_css": {
      "key": "ckan.site_custom_css",
      "prev_value": "",
      "updated_at": "2023-07-26T08:34:26.372150",
      "value": "body{color: red;}"
    }
  },
  "revert": {
    "ckan.site_title": {
      "key": "ckan.site_title",
      "prev_value": "CKAN",
      "updated_at": "2023-07-26T08:35:25.536150",
      "value": "Updated"
    }
  }
}

```

## Troubleshooting

> Changing `debug` or beaker-related options has no effect.

Most of options are checked by CKAN in runtime, when request is made. But
beaker settings, debug flag and a number of other options are used when WSGI
application is created and these options cannot be changed in runtime at the
moment. CKAN core requires some essential changes in initialization workflow
and additional safety measures before it become possible.

We'll consider expediency of this possibility in future, but for now this
problem has a low priority, so some options just should never be changed in
runtime.

> Changing `ckan.plugins` works with actions/validators/helpers, but not with
> middlewares or blueprints.

It falls under the previous problem. A number of plugin hooks are used when
application is initialized, namely: middlewares, blueprints, CLI commands and
translations. There is no reliable way to reset these items in runtime. So only
plugins that are not using corresponding interfaces can be enabled/disabled via
editable config.

But even if plugin can be safely enabled, it's not recommended. Modifying
plugins list via editable config may lead to changes in plugins order, which in
turn may cause other hard-to-track bugs. Finally, there is no way to tell
whether all the requirements of plugin are satisfied, so enabling/disabling it
in runtime potentially can break the whole application.

> Some options(ones that customized via built in AdminUI of CKAN) cannot be
> changed.

This plugin is not compatible with the CKAN's built-in AdminUI Config
form. Results are unpredictable when they are combined, so prefer to `Reset`
built-in config form and never use it if you going to rely on this plugin. Or,
at least, do not change the config option managed by AdminUI using the plugin's
API. There is an option that automatically saves any modifications from native
AdminUI as editable config options and then resets native AdminUI:
`ckanext.editable_config.convert_core_overrides`.


> Option saved with a value that prevent further modifications/breaks application.

You can either clean `editable_config_option` table removing all customizations
or just "bad" ones. Or you can combine
[ckanapi](https://pypi.org/project/ckanapi/) and environment variable
`CKANEXT_EDITABLE_CONFIG_DISABLE` in order to disable `editable_config` effect
and remove overrides via API:
```sh
CKANEXT_EDITABLE_CONFIG_DISABLE=1 ckanapi action editable_config_revert keys=BAD_OPTION_NAME
```


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
