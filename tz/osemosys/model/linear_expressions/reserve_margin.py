from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_reserve_margin(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    TotalCapacityInReserveMargin = (
        (
            ds["ReserveMarginTagTechnology"] * ds["CapacityToActivityUnit"] * lex["GrossCapacity"]
        ).where(
            (ds["ReserveMargin"] > 0)
            & (ds["ReserveMarginTagTechnology"] == 1)
            & (ds["ReserveMarginTagTechnology"] * ds["CapacityToActivityUnit"]).notnull(),
            drop=False,
        )
    ).sum("TECHNOLOGY")

    RateOfProductionByTechnologyByModeWithReserveMargin = m["RateOfActivity"] * ds[
        "OutputActivityRatio"
    ].where(
        (ds["OutputActivityRatio"].notnull())
        & (ds["ReserveMargin"] > 0)
        & (ds["ReserveMarginTagFuel"] == 1)
        & (ds["ReserveMarginTagTechnology"] == 1),
        drop=False,
    )

    RateOfProductionByTechnologyWithReserveMargin = (
        RateOfProductionByTechnologyByModeWithReserveMargin.where(
            (ds["OutputActivityRatio"].notnull())
            & (ds["ReserveMargin"] > 0)
            & (ds["ReserveMarginTagFuel"] == 1)
            & (ds["ReserveMarginTagTechnology"] == 1),
            drop=False,
        ).sum(dims="MODE_OF_OPERATION")
    )

    RateOfProductionWithReserveMargin = RateOfProductionByTechnologyWithReserveMargin.where(
        (ds["OutputActivityRatio"].notnull())
        & (ds["ReserveMargin"] > 0)
        & (ds["ReserveMarginTagFuel"] == 1)
        & (ds["ReserveMarginTagTechnology"] == 1),
        drop=False,
    ).sum(dims="TECHNOLOGY")

    DemandNeedingReserveMargin = (
        (lex["RateOfProduction"] * ds["ReserveMarginTagFuel"])
        .where((ds["ReserveMargin"] > 0) & (ds["ReserveMarginTagFuel"] == 1), drop=False)
        .sum("FUEL")
    )

    lex.update(
        {
            "TotalCapacityInReserveMargin": TotalCapacityInReserveMargin,
            "RateOfProductionByTechnologyByModeWithReserveMargin": RateOfProductionByTechnologyByModeWithReserveMargin,  # noqa: E501
            "RateOfProductionByTechnologyWithReserveMargin": RateOfProductionByTechnologyWithReserveMargin,  # noqa: E501
            "RateOfProductionWithReserveMargin": RateOfProductionWithReserveMargin,
            "DemandNeedingReserveMargin": DemandNeedingReserveMargin,
        }
    )
