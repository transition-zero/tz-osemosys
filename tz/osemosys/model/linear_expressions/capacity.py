from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_capacity(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    NewCapacity = m["NewCapacity"].rename(YEAR="BUILDYEAR")

    mask = (ds.YEAR - NewCapacity.data.BUILDYEAR >= 0) & (
        ds.YEAR - NewCapacity.data.BUILDYEAR < ds.OperationalLife
    )

    AccumulatedNewCapacity = NewCapacity.where(mask).sum("BUILDYEAR")

    GrossCapacity = AccumulatedNewCapacity + ds["ResidualCapacity"].fillna(0)

    lex.update(
        {
            "NewCapacity": NewCapacity,
            "AccumulatedNewCapacity": AccumulatedNewCapacity,
            "GrossCapacity": GrossCapacity,
        }
    )
