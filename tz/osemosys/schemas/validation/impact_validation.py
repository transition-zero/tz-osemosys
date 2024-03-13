from tz.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max


def exogenous_annual_within_constraint(id, constraint_annual, exogenous_annual):
    """
    Check exogenous_annual <= constraint_annual for each region, impact and year
    """

    if exogenous_annual is not None and constraint_annual is not None:
        if not check_min_vals_lower_max(
            exogenous_annual,
            constraint_annual,
            ["REGION", "YEAR", "VALUE"],
        ):
            raise ValueError(
                f"Impact '{id}' values in exogenous_annual should be lower than"
                " or equal to the corresponding values in constraint_annual"
            )

    return True


def exogenous_total_within_constraint(id, constraint_total, exogenous_total):
    """
    Check exogenous_total <= constraint_total for each region and impact
    """

    if exogenous_total is not None and constraint_total is not None:
        if not check_min_vals_lower_max(
            exogenous_total,
            constraint_total,
            ["REGION", "VALUE"],
        ):
            raise ValueError(
                f"Impact '{id}' values in exogenous_total should be lower than"
                " or equal to the corresponding values in constraint_total"
            )

    return True
