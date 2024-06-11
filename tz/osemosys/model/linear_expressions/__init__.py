from typing import Dict

import xarray as xr
from linopy import LinearExpression, Model

from tz.osemosys.model.linear_expressions.activity import add_lex_activity
from tz.osemosys.model.linear_expressions.capacity import add_lex_capacity
from tz.osemosys.model.linear_expressions.discounting import add_lex_discounting
from tz.osemosys.model.linear_expressions.emissions import add_lex_emissions
from tz.osemosys.model.linear_expressions.financials import add_lex_financials
from tz.osemosys.model.linear_expressions.production import add_lex_quantities
from tz.osemosys.model.linear_expressions.reserve_margin import add_lex_reserve_margin
from tz.osemosys.model.linear_expressions.storage import add_lex_storage
from tz.osemosys.model.linear_expressions.trade import add_lex_trade


def add_linear_expressions(ds: xr.Dataset, m: Model) -> Dict[str, LinearExpression]:
    lex = {}

    add_lex_discounting(ds, m, lex)
    add_lex_activity(ds, m, lex)
    add_lex_capacity(ds, m, lex)
    if ds["EMISSION"].size > 0:
        add_lex_emissions(ds, m, lex)
    if ds["STORAGE"].size > 0:
        add_lex_storage(ds, m, lex)
    if ds["TradeRoute"].notnull().any():
        add_lex_trade(ds, m, lex)
    add_lex_financials(ds, m, lex)
    add_lex_quantities(ds, m, lex)
    add_lex_reserve_margin(ds, m, lex)

    return lex
