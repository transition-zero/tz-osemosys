from feo.osemosys.schemas.validation.common_validation import check_min_vals_lower_max


def technology_validation(values):
    id = values.get("id")
    values.get("capacity_activity_unit_ratio")
    values.get("capacity_one_tech_unit")
    values.get("availability_factor")
    values.get("capacity_factor")
    values.get("operating_life")
    values.get("capex")
    values.get("opex_fixed")
    values.get("opex_variable")
    values.get("residual_capacity")
    capacity_gross_max = values.get("capacity_gross_max")
    capacity_gross_min = values.get("capacity_gross_min")
    capacity_additional_max = values.get("capacity_additional_max")
    capacity_additional_min = values.get("capacity_additional_min")
    activity_annual_max = values.get("activity_annual_max")
    activity_annual_min = values.get("activity_annual_min")
    activity_total_max = values.get("activity_total_max")
    activity_total_min = values.get("activity_total_min")
    values.get("emission_activity_ratio")
    values.get("input_activity_ratio")
    values.get("output_activity_ratio")
    values.get("to_storage")
    values.get("from_storage")
    values.get("is_renewable")

    # Check minimum activity constraints are lower than maximum activity constraints
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

    # Check minimum capacity constraints are lower than maximum capacity constraints
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


def technology_storage_validation(values):
    values.get("capex")
    values.get("operating_life")
    values.get("minimum_charge")
    values.get("initial_level")
    values.get("residual_capacity")
    values.get("max_discharge_rate")
    values.get("max_charge_rate")

    return values