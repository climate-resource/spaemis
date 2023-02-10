from openscm_units import unit_registry

if not hasattr(unit_registry, "hydrogen"):  # pragma: no branch
    unit_registry.define("H = [hydrogen] = H2")
    unit_registry.define("hydrogen = H")
    unit_registry.define("t{symbol} = t * {symbol}".format(symbol="H"))
