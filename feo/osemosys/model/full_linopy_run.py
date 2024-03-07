import os
import re

# Suppress FutureWarning messages
import warnings

from otoole import read
from otoole.utils import _read_file

warnings.simplefilter(action="ignore", category=FutureWarning)

import logging

import xarray as xr
from linopy import Model

from feo.osemosys.model.constraints.accounting_technology import *
from feo.osemosys.model.constraints.annual_activity import *
from feo.osemosys.model.constraints.capacity_adequacy_a import *
from feo.osemosys.model.constraints.capacity_adequacy_b import *
from feo.osemosys.model.constraints.capital_costs import *

# Constraints
from feo.osemosys.model.constraints.demand import *
from feo.osemosys.model.constraints.emissions import *
from feo.osemosys.model.constraints.energy_balance_a import *
from feo.osemosys.model.constraints.energy_balance_b import *
from feo.osemosys.model.constraints.new_capacity import *
from feo.osemosys.model.constraints.operating_costs import *
from feo.osemosys.model.constraints.re_targets import *
from feo.osemosys.model.constraints.reserve_margin import *
from feo.osemosys.model.constraints.salvage_value import *
from feo.osemosys.model.constraints.total_activity import *
from feo.osemosys.model.constraints.total_capacity import *
from feo.osemosys.model.constraints.total_discounted_costs import *

# Variables
from feo.osemosys.model.variables.activity import *
from feo.osemosys.model.variables.capacity import *
from feo.osemosys.model.variables.demand import *
from feo.osemosys.model.variables.emissions import *
from feo.osemosys.model.variables.other import *
from feo.osemosys.model.variables.storage import *

# RunSpec


logger = logging.getLogger(__name__)


def create_and_run_linopy(model_name: str, annotated_lp=False):
    config_path = os.path.join("examples/otoole_config_files", f"{model_name}.yaml")

    folder_path = os.path.join("examples/otoole_csvs", model_name)

    (
        ds,
        m,
        discount_factor,
        discount_factor_mid,
        discount_factor_idv,
        discount_factor_mid_idv,
        pv_annuity,
        capital_recovery_factor,
    ) = create_base_linopy_model(config_path, folder_path)

    m = add_linopy_variables(ds, m)

    m = add_linopy_constraints(
        ds,
        m,
        discount_factor,
        discount_factor_mid,
        discount_factor_idv,
        discount_factor_mid_idv,
        pv_annuity,
        capital_recovery_factor,
    )

    m = run_linopy_model(m, model_name)

    if annotated_lp:
        write_annotated_lp(m, model_name)
    return m


def create_base_linopy_model(config_path: str, folder_path: str):
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
    discount_factor_idv = (1 + ds["DiscountRateIdv"]) ** (
        ds.coords["YEAR"] - min(ds.coords["YEAR"])
    )
    discount_factor_mid_idv = (1 + ds["DiscountRateIdv"]) ** (
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
    return (
        ds,
        m,
        discount_factor,
        discount_factor_mid,
        discount_factor_idv,
        discount_factor_mid_idv,
        pv_annuity,
        capital_recovery_factor,
    )


def add_linopy_variables(ds: xr.Dataset, m: Model) -> Model:
    m = add_activity_variables(ds, m)
    m = add_capacity_variables(ds, m)
    m = add_demand_variables(ds, m)
    m = add_emission_variables(ds, m)
    m = add_other_variables(ds, m)
    # m = add_storage_variables(ds, m)
    return m


def add_linopy_constraints(
    ds: xr.Dataset,
    m: Model,
    discount_factor: float,
    discount_factor_mid: float,
    discount_factor_idv: float,
    discount_factor_mid_idv: float,
    pv_annuity: float,
    capital_recovery_factor: float,
) -> Model:
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


def run_linopy_model(m: Model, model_name: str):
    # Solve Model
    results_path = f"../results/{model_name}/"
    if not os.path.exists(results_path):
        os.makedirs(results_path)

    # m.to_file(f"../results/{model_name}/{model_name}.lp")

    m.solve(solver_name="cbc", log_fn=f"../results/{model_name}/solver.log")
    return m


def write_annotated_lp(m: Model, model_name: str):
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
                # if idx > 1789554:
                #    break


