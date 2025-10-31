from collections import defaultdict
from typing import TYPE_CHECKING

from tz.osemosys.schemas.validation.validation_utils import check_min_vals_lower_max

if TYPE_CHECKING:
    from tz.osemosys import Technology


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

        if (
            technology.production_target_min is not None
            and technology.production_target_max is not None
        ):
            if not check_min_vals_lower_max(
                technology.production_target_min,
                technology.production_target_max,
                ["REGION", "FUEL", "YEAR", "VALUE"],
            ):
                raise ValueError(
                    f"Minimum production target (production_target_min) is not less than maximum "
                    f"production target (production_target_max) for technology '{technology.id}'."
                )


def validate_technology_production_target_commodities(technology: "Technology") -> None:
    """Check that the commodities defined in the technology's production targets
    are actually produced by the technology.
    """
    commodities = set()
    for mode in technology.operating_modes:
        if mode.output_activity_ratio is not None:
            for values in mode.output_activity_ratio.data.values():
                commodities.update(values.keys())

    if not commodities and (
        technology.production_target_max is not None or technology.production_target_min is not None
    ):
        raise ValueError(
            f"Technology '{technology.id}' does not produce any commodities, but it "
            "has one or more production target defined."
        )

    if technology.production_target_max is not None:
        for values in technology.production_target_max.data.values():
            for commodity in values:
                if commodity not in commodities:
                    raise ValueError(
                        f"Technology '{technology.id}' has a production target defined for "
                        f"commodity '{commodity}', but it does not produce this commodity."
                    )

    if technology.production_target_min is not None:
        for values in technology.production_target_min.data.values():
            for commodity in values:
                if commodity not in commodities:
                    raise ValueError(
                        f"Technology '{technology.id}' has a production target defined for "
                        f"commodity '{commodity}', but it does not produce this commodity."
                    )


def validate_technologies_production_targets_values(
    technologies: list["Technology"],
) -> None:
    """Check that the sum of all minimum production targets at each node for each commodity
    in each year is less than or equal to 1.0.
    """
    totals = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for technology in technologies:
        if technology.production_target_min is not None:
            for node, commodities in technology.production_target_min.data.items():
                for commodity, years in commodities.items():
                    for year, value in years.items():
                        totals[node][commodity][year] += value
                        if totals[node][commodity][year] > 1.0:
                            raise ValueError(
                                f"Total minimum production target for {node, commodity, year} "
                                f"exceeds 1.0."
                            )


def validate_technologies_reserve_margin_tag(technologies: list["Technology"]) -> None:
    """Check that if include_in_joint_reserve_margin is defined, it takes values between 0 and 1."""
    for technology in technologies:
        if technology.include_in_joint_reserve_margin is not None:
            for region_values in technology.include_in_joint_reserve_margin.data.values():
                for value in region_values.values():
                    if not (0.0 <= value <= 1.0):
                        raise ValueError(
                            f"include_in_joint_reserve_margin for technology '{technology.id}' "
                            f"must be between 0 and 1 inclusive."
                        )
