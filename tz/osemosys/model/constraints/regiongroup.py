from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_regiongroup_constraints(
    ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]
) -> Model:

    con = lex["AnnualEmissionsRegionGroup"].fillna(0) <= ds["AnnualEmissionLimitRegionGroup"] - ds[
        "AnnualExogenousEmissionRegionGroup"
    ].fillna(0)
    mask = (ds["AnnualEmissionLimitRegionGroup"] != -1) & (
        ds["AnnualEmissionLimitRegionGroup"].notnull()
    )

    m.add_constraints(con, name="E10_AnnualEmmissionsLimitRegionGroup", mask=mask)

    con = lex["ProductionAnnualRERegionGroupAggregate"] >= (
        lex["ProductionAnnualRegionGroupAggregate"] * ds["RegionGroupREMinProductionTarget"]
    )
    mask = ds["RETagFuel"] == 1
    m.add_constraints(con, name="RE2_RegionGroup_RenewableProduction_MinConstraint", mask=mask)

    return m
