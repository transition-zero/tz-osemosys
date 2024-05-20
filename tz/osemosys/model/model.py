from typing import Dict, Optional

import xarray as xr
from linopy import LinearExpression
from linopy import Model as LPModel
from linopy import available_solvers

from tz.osemosys.io.load_model import load_cfg
from tz.osemosys.model.constraints import add_constraints
from tz.osemosys.model.linear_expressions import add_linear_expressions
from tz.osemosys.model.objective import add_objective
from tz.osemosys.model.variables import add_variables
from tz.osemosys.schemas import RunSpec

SOLUTION_KEYS = [
    "AnnualFixedOperatingCost",
    "AnnualVariableOperatingCost",
    "CapitalInvestment",
    "CapitalInvestmentStorage",
    "DemandNeedingReserveMargin",
    "DiscountedCapitalInvestment",
    "DiscountedCapitalInvestmentStorage",
    "DiscountedOperatingCost",
    "DiscountedSalvageValue",
    "GrossStorageCapacity",
    "NetCharge",
    "NewCapacity",
    "NewStorageCapacity",
    "NumberOfNewTechnologyUnits",
    "OperatingCost",
    "Production",
    "SalvageValue",
    "StorageLevel",
    "TotalAnnualTechnologyActivityByMode",
    "GrossCapacity",
    "TotalCapacityInReserveMargin",
    "TotalDiscountedCost",
    "TotalDiscountedCostByTechnology",
    "TotalDiscountedStorageCost",
    "TotalTechnologyAnnualActivity",
    "TotalTechnologyModelPeriodActivity",
    "Trade",
    "Use",
    "marginal_cost_of_demand",
    "marginal_cost_of_demand_annual",
    "marginal_cost_of_emissions_total",
    "marginal_cost_of_emissions_annual",
]


class Model(RunSpec):
    _data: xr.Dataset
    _m: LPModel
    _linear_expressions: Dict[str, LinearExpression]
    _solution: Optional[xr.Dataset] = None
    _objective: Optional[float] = None
    _objective_constant: Optional[float] = None

    @classmethod
    def from_yaml(cls, *spec_files):
        cfg = load_cfg(*spec_files)
        return cls(**cfg)

    def _build_dataset(self):
        data = self.to_xr_ds()
        return data

    def _build_model(self):
        self._m = LPModel(force_dim_names=True)
        add_variables(self._data, self._m)
        self._linear_expressions = add_linear_expressions(self._data, self._m)
        add_constraints(self._data, self._m, self._linear_expressions)
        self._objective_constant = add_objective(self._m, self._linear_expressions)

    def _build(self):
        self._data = self._build_dataset()
        self._build_model()

    def _get_solution(self, solution_vars: list[str] | str | None = None):

        # construct duals separately
        duals = xr.Dataset(
            {
                key: getattr(self._m.constraints, key).dual
                for key in [
                    "EBa11_EnergyBalanceEachTS5_alt",
                    "EBb4_EnergyBalanceEachYear4",
                ]
            }
        )

        duals = duals.merge(
            xr.Dataset(
                {
                    key: getattr(self._m.constraints, key).dual
                    for key in [
                        "E8_AnnualEmissionsLimit",
                        "E9_ModelPeriodEmissionsLimit",
                    ]
                    if hasattr(self._m.constraints, key)
                }
            )
        )

        duals = duals.rename(
            dict(
                zip(
                    [
                        "EBa11_EnergyBalanceEachTS5_alt",
                        "EBb4_EnergyBalanceEachYear4",
                    ],
                    [
                        "marginal_cost_of_demand",
                        "marginal_cost_of_demand_annual",
                    ],
                )
            )
        )
        if "E8_AnnualEmissionsLimit" in duals and "E9_ModelPeriodEmissionsLimit" in duals:
            duals = duals.rename(
                dict(
                    zip(
                        [
                            "E8_AnnualEmissionsLimit",
                            "E9_ModelPeriodEmissionsLimit",
                        ],
                        [
                            "marginal_cost_of_emissions_annual",
                            "marginal_cost_of_emissions_total",
                        ],
                    )
                )
            )

        # also merge on StorageLevel after unstacking
        solution_base = self._m.solution.merge(
            xr.Dataset(
                {
                    k: v.solution
                    for k, v in self._linear_expressions.items()
                    if (
                        (k not in self._m.solution)
                        and (hasattr(v, "solution"))
                        and ("YRTS" not in v.coords)
                    )
                }
            )
        ).merge(duals)

        if "StorageLevel" in self._linear_expressions:
            solution_base = solution_base.merge(
                self._linear_expressions["StorageLevel"]
                .solution.unstack("YRTS")
                .rename("StorageLevel")
            )

        if solution_vars is None:
            return xr.Dataset(
                {
                    k: solution_base[k]
                    for k in sorted(list(solution_base.keys()))
                    if k in SOLUTION_KEYS
                }
            )
        elif solution_vars == "all":
            return xr.Dataset({k: solution_base[k] for k in sorted(list(solution_base.keys()))})
        else:
            # ensure TotalDiscountedCost is always included
            if "TotalDiscountedCost" not in solution_vars:
                solution_vars.append("TotalDiscountedCost")
            return xr.Dataset({k: solution_base[k] for k in solution_vars})

    def solve(
        self,
        solver: str | None = None,
        lp_path: str | None = None,
        io_api: str = "lp",
        log_fn: str | None = None,
        solution_vars: list[str] | str | None = None,
    ):
        self._build()

        if solver is None:
            solver = available_solvers[0]
        else:
            assert (
                solver in available_solvers
            ), f"Solver {solver} not available. Choose from {available_solvers}."

        if lp_path:
            self._m.to_file(lp_path)

        self._m.solve(solver_name=solver, io_api=io_api, log_fn=log_fn)

        if self._m.termination_condition == "optimal":
            self._solution = self._get_solution(solution_vars)

        # rather hacky - constants not currently supported in objective functions:
        # https://github.com/PyPSA/linopy/issues/236
        # TODO: find out why and add constant back on: + self._objective_constant
        self._objective = self._solution.TotalDiscountedCost.sum().values

        return True

    @property
    def solution(self):
        return self._solution

    @property
    def objective(self):
        if not self._objective:
            raise ValueError("Model has not been solved yet or the solution is not optimal.")
        return self._objective
