from linopy import LinearExpression, Model


def add_objective(m: Model, lex: dict[str, LinearExpression]) -> float:
    objective = lex["TotalDiscountedCost"].sum(dims=["REGION", "YEAR"])

    # constants not currently supported in objective functions:
    # https://github.com/PyPSA/linopy/issues/236
    if (objective.const != 0).any():
        objective_constant = objective.const.item()
        objective.const.values = 0
    else:
        objective_constant = 0

    m.add_objective(expr=objective, overwrite=True)
    return objective_constant
