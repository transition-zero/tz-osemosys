from feo.osemosys.schemas.validation.common_validation import check_sums_one


def commodity_validation(values):
    demand_profile = values.get("demand_profile")

    # Check demand_profile sums to one, within leniency
    if demand_profile is not None:
        check_sums_one(
            data=demand_profile.data,
            leniency=0.01,
            cols=["REGION", "TIMESLICE", "YEAR", "VALUE"],
            cols_to_groupby=["REGION", "YEAR"],
        )

    return values
