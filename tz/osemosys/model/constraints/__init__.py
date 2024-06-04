from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model

from .annual_activity import add_annual_activity_constraints
from .capacity_adequacy_a import add_capacity_adequacy_a_constraints
from .capacity_adequacy_b import add_capacity_adequacy_b_constraints
from .capacity_growth_rate import add_capacity_growthrate_constraints
from .emissions import add_emissions_constraints
from .energy_balance_a import add_energy_balance_a_constraints
from .energy_balance_b import add_energy_balance_b_constraints
from .new_capacity import add_new_capacity_constraints
from .re_targets import add_re_targets_constraints
from .reserve_margin import add_reserve_margin_constraints
from .storage import add_storage_constraints
from .total_activity import add_total_activity_constraints
from .total_capacity import add_total_capacity_constraints
from .trade import add_trade_constraints


def add_constraints(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]) -> Model:
    """Add all constraints to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model
    """

    # restore one at a time
    m = add_capacity_adequacy_a_constraints(ds, m, lex)
    m = add_capacity_adequacy_b_constraints(ds, m, lex)
    m = add_energy_balance_a_constraints(ds, m, lex)
    m = add_energy_balance_b_constraints(ds, m, lex)
    m = add_emissions_constraints(ds, m, lex)
    m = add_annual_activity_constraints(ds, m, lex)
    m = add_new_capacity_constraints(ds, m, lex)
    m = add_re_targets_constraints(ds, m, lex)
    m = add_reserve_margin_constraints(ds, m, lex)
    m = add_storage_constraints(ds, m, lex)
    m = add_total_activity_constraints(ds, m, lex)
    m = add_total_capacity_constraints(ds, m, lex)
    m = add_capacity_growthrate_constraints(ds, m, lex)
    m = add_trade_constraints(ds, m, lex)

    return m
