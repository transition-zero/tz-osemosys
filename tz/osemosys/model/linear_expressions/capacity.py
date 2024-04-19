from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model


def add_lex_capacity(ds: xr.Dataset, m: Model, lex: Dict[str, LinearExpression]):
    NewCapacity = m["NewCapacity"].rename(YEAR="BUILDYEAR")

    lex.update(
        {
            "NewCapacity": NewCapacity,
        }
    )
