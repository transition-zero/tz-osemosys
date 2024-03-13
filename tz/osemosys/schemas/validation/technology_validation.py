from tz.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max


def min_activity_lower_than_max(values):
    """
    Check minimum activity constraints are lower than maximum activity constraints
    """
    id = values.get("id")
    activity_annual_max = values.get("activity_annual_max")
    activity_annual_min = values.get("activity_annual_min")
    activity_total_max = values.get("activity_total_max")
    activity_total_min = values.get("activity_total_min")

    if activity_annual_min is not None and activity_annual_max is not None:
        check_min_vals_lower_max(
            activity_annual_min,
            activity_annual_max,
            ["REGION", "YEAR", "VALUE"],
            (
                f"Technology {id} values in activity_annual_min should be lower than "
                "or equal to the corresponding values in activity_annual_max"
            ),
        )
    if activity_total_min is not None and activity_total_max is not None:
        check_min_vals_lower_max(
            activity_total_min,
            activity_total_max,
            ["REGION", "VALUE"],
            (
                f"Technology {id} values in activity_total_min should be lower than "
                "or equal to the corresponding values in activity_total_max"
            ),
        )

    return values


def min_capacity_lower_than_max(values):
    """
    Check minimum capacity constraints are lower than maximum capacity constraints
    """
    id = values.get("id")
    capacity_gross_max = values.get("capacity_gross_max")
    capacity_gross_min = values.get("capacity_gross_min")
    capacity_additional_max = values.get("capacity_additional_max")
    capacity_additional_min = values.get("capacity_additional_min")

    if capacity_additional_min is not None and capacity_additional_max is not None:
        check_min_vals_lower_max(
            capacity_additional_min,
            capacity_additional_max,
            ["REGION", "YEAR", "VALUE"],
            (
                f"Technology {id} values in capacity_additional_min should be lower than "
                "or equal to the corresponding values in capacity_additional_max"
            ),
        )
    if capacity_gross_min is not None and capacity_gross_max is not None:
        check_min_vals_lower_max(
            capacity_gross_min,
            capacity_gross_max,
            ["REGION", "YEAR", "VALUE"],
            (
                f"Technology {id} values in capacity_gross_min should be lower than "
                "or equal to  the corresponding values in capacity_gross_max"
            ),
        )

    return values
