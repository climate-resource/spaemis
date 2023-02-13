"""
Scalers

A scaler is an object that performs some kind of scaling upon a dataset (typically inventory
data). This scaling operation is generally to update data for a variable/sector
to some future time-base.

A number of different scalers exist with the most simple of all being a :class:`ConstantScaler`.
This constant scaler is will apply some static scale factor to the underlying data.
"""
from typing import Type

from spaemis.config import ScalerMethod

from .base import BaseScaler
from .constant import ConstantScaler
from .relative_change import RelativeChangeScaler

_scalers = {"constant": ConstantScaler, "relative_change": RelativeChangeScaler}


def get_scaler(name: str) -> Type[BaseScaler]:
    """
    Get a scaler by name

    Parameters
    ----------
    name
        Name of the scaler

        Options include:
        * "constant": Apply a constant multiplier

    Raises
    ------
    ValueError:
        An unknown scaler is requested

    Returns
    -------
    The class of the scaler of interest
    """
    try:
        return _scalers[name]
    except KeyError as exc:
        raise ValueError(f"Unknown scaler: {name}") from exc


def get_scaler_by_config(method: ScalerMethod) -> BaseScaler:
    """
    Create a scaler from configuration

    Parameters
    ----------
    method:
        Configuration which includes information about which scaler to use and
        how to initialise it.

    Returns
    -------
    A scaler ready for use
    """
    cls = get_scaler(method.name)

    return cls.create_from_config(method)
