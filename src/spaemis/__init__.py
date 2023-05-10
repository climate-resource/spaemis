"""
spaemis a tool for generating future emissions for local air quality modelling

See README and docs for more info.
"""
from importlib.metadata import version as _version

try:
    __version__ = _version("spaemis")
except Exception:  # pylint: disable=broad-except pragma: no cover
    # Local copy, not installed with setuptools
    __version__ = "unknown"


import spaemis.unit_registry  # noqa
