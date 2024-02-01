from feo.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max


def impact_validation(values):
    constraint_annual = values.get("constraint_annual")
    constraint_total = values.get("constraint_total")
    exogenous_annual = values.get("exogenous_annual")
    exogenous_total = values.get("exogenous_total")

    # Check exogenous_annual <= constraint_annual for each region, impact and year
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

    # Check exogenous_total <= constraint_total for each region and impact
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
