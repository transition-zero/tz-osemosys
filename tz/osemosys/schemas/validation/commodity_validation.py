from tz.osemosys.schemas.validation.validation_utils import check_sums_one


def demand_profile_sums_one(values):
    """
    Check that demand_profile sums to one, within allowed leniency
    """
    demand_profile = values.get("demand_profile")

    if demand_profile is not None:
        check_sums_one(
            data=demand_profile.data,
            leniency=0.05,
            cols=["REGION", "TIMESLICE", "YEAR", "VALUE"],
            cols_to_groupby=["REGION", "YEAR"],
        )

    return values
