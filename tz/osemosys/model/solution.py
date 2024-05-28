from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model

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
    # "Trade",
    "NetTrade",
    "Import",
    "Export",
    "Use",
    "marginal_cost_of_demand",
    "marginal_cost_of_demand_annual",
    "marginal_cost_of_emissions_total",
    "marginal_cost_of_emissions_annual",
]


def build_solution(
    m: Model, lex: Dict[str, LinearExpression], solution_vars: list[str] | str | None = None
):

    # construct duals separately
    duals = xr.Dataset(
        {
            key: getattr(m.constraints, key).dual
            for key in [
                "EBa11_EnergyBalanceEachTS5_trn",
                "EBb4_EnergyBalanceEachYear4",
            ]
        }
    )

    duals = duals.merge(
        xr.Dataset(
            {
                key: getattr(m.constraints, key).dual
                for key in [
                    "E8_AnnualEmissionsLimit",
                    "E9_ModelPeriodEmissionsLimit",
                ]
                if hasattr(m.constraints, key)
            }
        )
    )

    duals = duals.rename(
        dict(
            zip(
                [
                    "EBa11_EnergyBalanceEachTS5_trn",
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
    solution_base = m.solution.merge(
        xr.Dataset(
            {
                k: v.solution
                for k, v in lex.items()
                if ((k not in m.solution) and (hasattr(v, "solution")) and ("YRTS" not in v.coords))
            }
        )
    ).merge(duals)

    if "StorageLevel" in lex:
        solution_base = solution_base.merge(
            lex["StorageLevel"].solution.unstack("YRTS").rename("StorageLevel")
        )

    if solution_vars is None:
        return xr.Dataset(
            {k: solution_base[k] for k in sorted(list(solution_base.keys())) if k in SOLUTION_KEYS}
        )
    elif solution_vars == "all":
        return xr.Dataset({k: solution_base[k] for k in sorted(list(solution_base.keys()))})
    else:
        # ensure TotalDiscountedCost is always included
        if "TotalDiscountedCost" not in solution_vars:
            solution_vars.append("TotalDiscountedCost")
        return xr.Dataset({k: solution_base[k] for k in solution_vars})