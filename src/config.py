"""Shared paths and configuration loading."""
import os
from functools import lru_cache

import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def asset_path(*parts):
    """Return an absolute path to a file shipped next to the source code."""
    return os.path.join(BASE_DIR, *parts)


@lru_cache(maxsize=None)
def load_config():
    with open(asset_path("config.yaml")) as f:
        return yaml.safe_load(f)
