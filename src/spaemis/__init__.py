"""
H2-adjust, a tool for producing a coherent set of emissions including H2.
See README and docs for more info.
"""


try:
    from importlib.metadata import version as _version
except ImportError:  # pragma: no cover
    # no recourse if the fallback isn't there either...
    from importlib_metadata import version as _version

try:
    __version__ = _version("spaemis")
except Exception:  # pylint: disable=broad-except pragma: no cover
    # Local copy, not installed with setuptools
    __version__ = "unknown"
