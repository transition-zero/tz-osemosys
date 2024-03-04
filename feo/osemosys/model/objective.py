from linopy import Model


def add_objective(m: Model) -> Model:
    objective = m["TotalDiscountedCost"].sum(dims=["REGION", "YEAR"])
    m.add_objective(expr=objective, overwrite=True)

    return m
