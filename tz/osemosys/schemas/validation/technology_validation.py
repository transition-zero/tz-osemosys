from tz.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max


def validate_min_lt_max(technologies):

    for technology in technologies:

        if technology.capacity_gross_min is not None and technology.capacity_gross_max is not None:
            if not check_min_vals_lower_max(
                technology.capacity_gross_min,
                technology.capacity_gross_max,
                ["REGION", "YEAR", "VALUE"],
            ):
                raise ValueError(
                    f"Minimum gross capacity (capacity_gross_min) is not less than maximum gross "
                    f"capacity (capacity_gross_max) for technology '{technology.id}'."
                )

        if (
            technology.capacity_additional_min is not None
            and technology.capacity_additional_max is not None
        ):
            if not check_min_vals_lower_max(
                technology.capacity_additional_min,
                technology.capacity_additional_max,
                ["REGION", "YEAR", "VALUE"],
            ):
                raise ValueError(
                    f"Minimum additional capacity (capacity_additional_min) is not less than "
                    f"maximum additional capacity (capacity_additional_max) for technology "
                    f"'{technology.id}'."
                )

        if (
            technology.activity_annual_min is not None
            and technology.activity_annual_max is not None
        ):
            if not check_min_vals_lower_max(
                technology.activity_annual_min,
                technology.activity_annual_max,
                ["REGION", "YEAR", "VALUE"],
            ):
                raise ValueError(
                    f"Minimum annual activity (activity_annual_min) is not less than maximum annual"
                    f" activity (activity_annual_max) for technology '{technology.id}'."
                )

        if technology.activity_total_min is not None and technology.activity_total_max is not None:
            if not check_min_vals_lower_max(
                technology.activity_total_min,
                technology.activity_total_max,
                ["REGION", "VALUE"],
            ):
                raise ValueError(
                    f"Minimum total activity (activity_total_min) is not less than maximum total "
                    f"activity (activity_total_max) for technology '{technology.id}'."
                )

        if technology.residual_capacity is not None and technology.capacity_gross_max is not None:

            if not check_min_vals_lower_max(
                technology.residual_capacity,
                technology.capacity_gross_max,
                ["REGION", "YEAR", "VALUE"],
            ):
                raise ValueError(
                    f"Residual capacity is greater than the allowed total installed capacity "
                    f"defined in capacity_gross_max for technology '{technology.id}'."
                )
