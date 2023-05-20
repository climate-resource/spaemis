"""
Unit Registry

Adds H2 related units if they haven't been previously registered
"""
from __future__ import annotations

import pint
from openscm_units import unit_registry  # type: ignore

if not hasattr(unit_registry, "hydrogen"):  # pragma: no branch
    unit_registry.define("H = [hydrogen] = H2")
    unit_registry.define("hydrogen = H")
    unit_registry.define("t{symbol} = t * {symbol}".format(symbol="H"))

unit_registry.define("cell = [cell]")


def convert_to_target_unit(
    initial_unit: str | pint.Unit | pint.Quantity[float],
    target_unit: str | pint.Unit,
) -> pint.Quantity[float]:
    """
    Calculate the scale factor required to convert between units

    This function supports converting a subset of the input units dimensions which
    is helpful in situations where arbitary dimensions can be provided i.e. Mt X/yr
    where X could be a range of species.

    >>> value = ur.Quantity(12, "Mt CH4/yr")
    >>> scale_factor = convert_to_target_unit(value.units, target_unit="kg")
    >>> ur.Quantity(value.m * scale_factor.m, scale_factor.u)

    Parameters
    ----------
    initial_unit
        Units of input
    target_unit
        The expected output

        Any dimensions present in the initial_unit, but not in the target unit will
        be kept the same.

    Returns
    -------
    pint.Quantity
        The magnitude of the quantity represents the required scale factor
        The units of the quantity represent the resulting unit
    """
    if isinstance(initial_unit, pint.Quantity):
        start = initial_unit
    else:
        start = unit_registry.Quantity(1, initial_unit)

    # Get pint to find the conversion factor for you
    start_in_target = (
        start / unit_registry.Quantity(1, target_unit)
    ).to_reduced_units()

    # Put the intended units back in
    correct_units: pint.Quantity[float] = start_in_target * unit_registry.Quantity(
        1.0, target_unit
    )
    return correct_units


__all__ = ["convert_to_target_unit", "unit_registry"]
