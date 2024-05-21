from copy import deepcopy
from typing import Dict

from linopy import LinearExpression, Model


def add_objective(m: Model, lex: Dict[str, LinearExpression]) -> Model:

    objective = lex["TotalDiscountedCost"].sum(dims=["REGION", "YEAR"])

    # constants not currently supported in objective functions:
    # https://github.com/PyPSA/linopy/issues/236
    if (objective.const != 0).any():
        objective_constant = deepcopy(objective.const)
        objective.const = 0
    else:
        objective_constant = 0

    m.add_objective(expr=objective, overwrite=True)

    return objective_constant
