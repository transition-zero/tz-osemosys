import logging
import os
import re
import warnings

import xarray as xr
from linopy import Model

try:
    from memory_profiler import profile
except ImportError:
    raise ImportError(
        "Please install memory_profiler to run this script: pip install memory_profiler"
    )
try:
    from otoole import read
except ImportError:
    raise ImportError("Please install otoole to run this script: pip install otoole")

from otoole.utils import _read_file

from tz.osemosys.model.constraints.accounting_technology import (
    add_accounting_technology_constraints,
)
from tz.osemosys.model.constraints.annual_activity import add_annual_activity_constraints
from tz.osemosys.model.constraints.capacity_adequacy_a import add_capacity_adequacy_a_constraints
from tz.osemosys.model.constraints.capacity_adequacy_b import add_capacity_adequacy_b_constraints
from tz.osemosys.model.constraints.capital_costs import add_capital_costs_constraints
from tz.osemosys.model.constraints.demand import add_demand_constraints
from tz.osemosys.model.constraints.emissions import add_emissions_constraints
from tz.osemosys.model.constraints.energy_balance_a import add_energy_balance_a_constraints
from tz.osemosys.model.constraints.energy_balance_b import add_energy_balance_b_constraints
from tz.osemosys.model.constraints.new_capacity import add_new_capacity_constraints
from tz.osemosys.model.constraints.operating_costs import add_operating_costs_constraints
from tz.osemosys.model.constraints.re_targets import add_re_targets_constraints
from tz.osemosys.model.constraints.reserve_margin import add_reserve_margin_constraints
from tz.osemosys.model.constraints.salvage_value import add_salvage_value_constraints
from tz.osemosys.model.constraints.total_activity import add_total_activity_constraints
from tz.osemosys.model.constraints.total_capacity import add_total_capacity_constraints
from tz.osemosys.model.constraints.total_discounted_costs import (
    add_total_discounted_costs_constraints,
)
from tz.osemosys.model.variables.activity import add_activity_variables
from tz.osemosys.model.variables.capacity import add_capacity_variables
from tz.osemosys.model.variables.demand import add_demand_variables
from tz.osemosys.model.variables.emissions import add_emission_variables
from tz.osemosys.model.variables.other import add_cost_variables

warnings.simplefilter(action="ignore", category=FutureWarning)

# RunSpec


logger = logging.getLogger(__name__)


@profile
def create_and_run_linopy(model_name: str, annotated_lp=False) -> Model:
    """Add demand constraint to the model

    Arguments
    ---------
    m: linopy.Model
        A linopy model
    annotated_lp: True / False
        Set whether to write an annotated LP file. Default is False.

    Returns
    -------
    linopy.Model


    Notes
    -----

    """
    config_path = os.path.join("examples/otoole_config_files", f"{model_name}.yaml")

    folder_path = os.path.join("examples/otoole_csvs", model_name)

    (
        ds,
        m,
        capital_recovery_factor,
        pv_annuity,
        discount_factor,
        discount_factor_mid,
    ) = create_base_linopy_model(config_path, folder_path)

    m = add_linopy_variables(ds, m)

    m = add_linopy_constraints(
        ds, m, capital_recovery_factor, pv_annuity, discount_factor, discount_factor_mid
    )

    m = run_linopy_model(m, model_name)

    if annotated_lp:
        write_annotated_lp(m, model_name)
    return m


@profile
def create_base_linopy_model(config_path: str, folder_path: str):
    """Create a Linopy model

    Arguments
    ---------
    m: linopy.Model
        A linopy model
    annotated_lp: True / False
        Set whether to write an annotated LP file. Default is False.

    Returns
    -------
    xarray.Dataset
    Linopy.Model
    capital_recovery_factor: float
    pv_annuity: float
    discount_factor: float
    discount_factor_mid: float


    Notes
    -----

    """
    # Open input data files
    with open(config_path) as config_file:
        config = _read_file(config_file, ".yaml")

    model, defaults = read(config_path, "csv", folder_path)

    # Reshape the CSV files to create the dataset of sets and parameters
    data_vars = {x: y.VALUE.to_xarray() for x, y in model.items() if config[x]["type"] == "param"}

    coords = {x: y.values.T[0] for x, y in model.items() if config[x]["type"] == "set"}

    ds = xr.Dataset(data_vars=data_vars, coords=coords)
    ds = ds.assign_coords({"_REGION": model["REGION"].values.T[0]})

    for param, default in defaults.items():
        if config[param]["type"] == "param":
            ds[param].attrs["default"] = default
            if default != 0:
                ds[param] = ds[param].fillna(default)

    # Initialise linopy model
    m = Model(force_dim_names=True)  # , chunk='auto')

    # Calculate financial coefficients
    discount_factor = (1 + ds["DiscountRate"]) ** (ds.coords["YEAR"] - min(ds.coords["YEAR"]))
    discount_factor_mid = (1 + ds["DiscountRate"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"]) + 0.5
    )

    pv_annuity = (
        (1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"])))
        * (1 + ds["DiscountRateIdv"])
        / ds["DiscountRateIdv"]
    )

    capital_recovery_factor_num = 1 - (1 + ds["DiscountRateIdv"]) ** (-1)
    capital_recovery_factor_den = 1 - (1 + ds["DiscountRateIdv"]) ** (-(ds["OperationalLife"]))

    capital_recovery_factor = capital_recovery_factor_num / capital_recovery_factor_den
    return (ds, m, capital_recovery_factor, pv_annuity, discount_factor, discount_factor_mid)


@profile
def add_linopy_variables(ds: xr.Dataset, m: Model) -> Model:
    """Add Linopy variables to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model

    Returns
    -------
    linopy.Model

    Notes
    -----

    """
    m = add_activity_variables(ds, m)
    m = add_capacity_variables(ds, m)
    m = add_demand_variables(ds, m)
    m = add_emission_variables(ds, m)
    m = add_cost_variables(ds, m)
    # m = add_storage_variables(ds, m)
    return m


@profile
def add_linopy_constraints(
    ds: xr.Dataset,
    m: Model,
    capital_recovery_factor: float,
    pv_annuity: float,
    discount_factor: float,
    discount_factor_mid: float,
) -> Model:
    """Add Linopy constraints to the model

    Arguments
    ---------
    ds: xarray.Dataset
        The parameters dataset
    m: linopy.Model
        A linopy model
    capital_recovery_factor: float
        Capital Recovery Factor
    pv_annuity: float
        PV Annuity
    discount_factor: float
        Discount factor
    discount_factor_mid: float
        Discount factor - mid-year

    Returns
    -------
    linopy.Model

    Notes
    -----

    """
    m = add_demand_constraints(ds, m)
    m = add_capacity_adequacy_a_constraints(ds, m)
    m = add_capacity_adequacy_b_constraints(ds, m)
    m = add_energy_balance_a_constraints(ds, m)
    m = add_energy_balance_b_constraints(ds, m)
    m = add_accounting_technology_constraints(ds, m)
    m = add_capital_costs_constraints(ds, m, capital_recovery_factor, pv_annuity, discount_factor)
    m = add_salvage_value_constraints(ds, m)
    m = add_operating_costs_constraints(ds, m, discount_factor_mid)
    m = add_total_discounted_costs_constraints(ds, m)
    m = add_total_capacity_constraints(ds, m)
    m = add_new_capacity_constraints(ds, m)
    m = add_annual_activity_constraints(ds, m)
    m = add_total_activity_constraints(ds, m)
    m = add_reserve_margin_constraints(ds, m)
    m = add_re_targets_constraints(ds, m)
    m = add_emissions_constraints(ds, m, discount_factor_mid)

    objective = m["TotalDiscountedCost"].sum(dims=["REGION", "YEAR"])
    m.add_objective(expr=objective, overwrite=True)
    return m


@profile
def run_linopy_model(m: Model, model_name: str) -> Model:
    """Run Linopy model

    Arguments
    ---------
    m: linopy.Model
        A linopy model
    model_name: str
        Name of reference model

    Returns
    -------
    linopy.Model


    Notes
    -----

    """
    # Solve Model
    results_path = f"../results/{model_name}/"
    if not os.path.exists(results_path):
        os.makedirs(results_path)

    # m.to_file(f"../results/{model_name}/{model_name}.lp")

    m.solve(solver_name="cbc", log_fn=f"../results/{model_name}/solver.log")
    return m


@profile
def write_annotated_lp(m: Model, model_name: str) -> Model:
    """Write an annotated LP file

    Arguments
    ---------
    m: linopy.Model
        A linopy model
    model_name: str
        Name of reference model

    Returns
    -------
    linopy.Model

    Notes
    -----

    """
    variable = re.compile("x[0-9]+")
    constraint = re.compile("c[0-9]+")

    with open(f"../results/{model_name}/annotated_{model_name}.lp", "w") as annotated:
        with open(f"../results/{model_name}/{model_name}.lp") as raw_lp_file:
            for idx, line in enumerate(raw_lp_file):
                vars = variable.search(line)
                cons = constraint.match(line)
                if cons:
                    label = int(cons.group(0)[1:])
                    name = m.constraints.get_name_by_label(label)
                    line = f"{name}:\n"
                if vars:
                    var = vars.group(0)
                    label = int(vars.group(0)[1:])
                    name = m.variables.get_name_by_label(label)
                    line = line.replace(var, name)
                annotated.write(line)
                if idx > 1789554:
                    break
