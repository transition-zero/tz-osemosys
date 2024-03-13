import xarray as xr
from linopy import Model

from .accounting_technology import add_accounting_technology_constraints
from .annual_activity import add_annual_activity_constraints
from .capacity_adequacy_a import add_capacity_adequacy_a_constraints
from .capacity_adequacy_b import add_capacity_adequacy_b_constraints
from .capital_costs import add_capital_costs_constraints
from .demand import add_demand_constraints
from .emissions import add_emissions_constraints
from .energy_balance_a import add_energy_balance_a_constraints
from .energy_balance_b import add_energy_balance_b_constraints
from .new_capacity import add_new_capacity_constraints
from .operating_costs import add_operating_costs_constraints
from .re_targets import add_re_targets_constraints
from .reserve_margin import add_reserve_margin_constraints
from .salvage_value import add_salvage_value_constraints
from .total_activity import add_total_activity_constraints
from .total_capacity import add_total_capacity_constraints
from .total_discounted_costs import add_total_discounted_costs_constraints


def add_constraints(ds: xr.Dataset, m: Model) -> Model:
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
    m = add_demand_constraints(ds, m)
    m = add_capacity_adequacy_a_constraints(ds, m)
    m = add_capacity_adequacy_b_constraints(ds, m)
    m = add_energy_balance_a_constraints(ds, m)
    m = add_energy_balance_b_constraints(ds, m)
    m = add_capital_costs_constraints(ds, m)
    m = add_emissions_constraints(ds, m)
    m = add_annual_activity_constraints(ds, m)
    m = add_accounting_technology_constraints(ds, m)
    m = add_new_capacity_constraints(ds, m)
    m = add_operating_costs_constraints(ds, m)
    m = add_re_targets_constraints(ds, m)
    m = add_reserve_margin_constraints(ds, m)
    m = add_salvage_value_constraints(ds, m)
    # m = add_storage_constraints(ds, m)
    m = add_total_activity_constraints(ds, m)
    m = add_total_capacity_constraints(ds, m)
    m = add_total_discounted_costs_constraints(ds, m)

    return m
