from feo.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max


def exogenous_annual_within_constraint(values):
    """
    Check exogenous_annual <= constraint_annual for each region, impact and year
    """
    constraint_annual = values.get("constraint_annual")
    exogenous_annual = values.get("exogenous_annual")

    if exogenous_annual is not None and constraint_annual is not None:
        check_min_vals_lower_max(
            exogenous_annual,
            constraint_annual,
            ["REGION", "YEAR", "VALUE"],
            (
                f"Impact {id} values in exogenous_annual should be lower than"
                " or equal tothe corresponding values in constraint_annual"
            ),
        )

    return values


def exogenous_total_within_constraint(values):
    """
    Check exogenous_total <= constraint_total for each region and impact
    """
    constraint_total = values.get("constraint_total")
    exogenous_total = values.get("exogenous_total")

    if exogenous_total is not None and constraint_total is not None:
        check_min_vals_lower_max(
            exogenous_total,
            constraint_total,
            ["REGION", "VALUE"],
            (
                f"Impact {id} values in exogenous_total should be lower than"
                " or equal to the corresponding values in constraint_total"
            ),
        )

    return values
