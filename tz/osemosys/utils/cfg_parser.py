import functools
import json
import os
import re

import yaml

from tz.osemosys import exceptions

from datetime import datetime, timedelta  # noqa


env_matcher = re.compile(r"\$ENV\{([^}^{]+)\}")
var_matcher = re.compile(r"\$\{([^}^{]+)\}")


def catch_os_env(env_var):
    try:
        return os.environ[env_var]
    except KeyError:
        raise exceptions.MissingVar(f"Missing environment variable: {env_var}")
    except Exception as e:
        raise e


def path_constructor(loader, node):
    txt = node.value
    for env_var in re.findall(env_matcher, node.value):
        txt = txt.replace(f"$ENV{{{env_var}}}", catch_os_env(env_var))

    return txt


class EnvVarLoader(yaml.SafeLoader):
    pass


EnvVarLoader.add_implicit_resolver("!path", env_matcher, None)
EnvVarLoader.add_constructor("!path", path_constructor)


def rsetattr(obj, attrs, val):
    pre = attrs[0:-1]
    post = attrs[-1]
    (rgetattr(obj, pre) if pre else obj)[post] = val
    return None


def rgetattr(obj, attrs, *args):
    def _getattr(obj, attr):
        if isinstance(obj, dict):
            return obj.get(attr)
        elif isinstance(obj, list):
            return obj[attr]

    return functools.reduce(_getattr, [obj] + attrs)


def recursive_keys(keys, input):
    if isinstance(input, dict):
        for key, value in input.items():
            if isinstance(value, dict):
                yield from recursive_keys(keys + [key], value)
            elif isinstance(value, list):
                yield from recursive_keys(keys + [key], value)
            else:
                yield keys + [key]
    elif isinstance(input, list):
        for key, value in enumerate(input):
            if isinstance(value, dict):
                yield from recursive_keys(keys + [key], value)
            elif isinstance(value, list):
                yield from recursive_keys(keys + [key], value)
            else:
                yield keys + [key]
    else:
        yield keys


def maybe_numeric(txt):
    try:
        return int(txt)
    except ValueError:
        try:
            return float(txt)
        except ValueError:
            return txt


def substitute_factory(cfg: dict):
    def _inner(key, val):
        def f(txt):
            if isinstance(txt, str):
                return maybe_numeric(txt.replace(f"${{{key}}}", str(val)))
            else:
                return txt

        return f

    recursive_keys({}, cfg)

    # get all keys that need replacing
    var_matcher = re.compile(r"\$\{([^}^{]+)\}")

    keys = [key for key in re.findall(var_matcher, json.dumps(cfg))]

    return [_inner(key, rgetattr(cfg, key.split("."))) for key in keys]


def walk_dict(d, f, *args):
    list_of_keys = recursive_keys([], d)

    changes_flag = False

    for sublist in list_of_keys:
        old_val = rgetattr(d, sublist)
        new_val = f(old_val, *args)
        rsetattr(d, sublist, new_val)
        changes_flag = changes_flag or (old_val != new_val)

    return changes_flag
