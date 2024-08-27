import pandas as pd


def check_tech_producing_commodity(values):
    """
    For each commodity, check there is a technology which produces it
    """
    for commodity in values.commodities:
        technology_missing = True
        for technology in values.technologies:
            for tech_mode in technology.operating_modes:
                if technology_missing and tech_mode.output_activity_ratio is not None:
                    for region in tech_mode.output_activity_ratio.data.keys():
                        if commodity.id in tech_mode.output_activity_ratio.data[region].keys():
                            technology_missing = False
        if technology_missing:
            raise ValueError(f"Commodity '{commodity.id}' is not an output of any technology")

    return values


def check_tech_producing_impact(values):
    """
    For each impact, check there is a technology which produces it
    """
    for impact in values.impacts:
        technology_missing = True
        for technology in values.technologies:
            for tech_mode in technology.operating_modes:
                if technology_missing and tech_mode.emission_activity_ratio is not None:
                    for region in tech_mode.emission_activity_ratio.data.keys():
                        if impact.id in tech_mode.emission_activity_ratio.data[region].keys():
                            technology_missing = False
        if technology_missing:
            raise ValueError(f"Impact '{impact.id}' is not an output of any technology")

    return values


def check_tech_consuming_commodity(values):
    """
    For each commodity which isn't a final demand, check it is the input of a technology
    """
    for commodity in values.commodities:
        if commodity.demand_annual is None:
            technology_missing = True
            for technology in values.technologies:
                for tech_mode in technology.operating_modes:
                    if technology_missing and tech_mode.input_activity_ratio is not None:
                        for region in tech_mode.input_activity_ratio.data.keys():
                            if commodity.id in tech_mode.input_activity_ratio.data[region].keys():
                                technology_missing = False
            if technology_missing:
                raise ValueError(
                    f"Commodity '{commodity.id}' is neither a final demand nor "
                    f"an input of any technology"
                )

    return values


def check_tech_linked_to_storage(values):
    """
    For each storage technology, check it is linked to at least one technology for charge/discharge
    """
    for storage in values.storage:
        techs_to_storage = []
        techs_from_storage = []
        for technology in values.technologies:
            for mode in technology.operating_modes:
                if mode.to_storage is not None:
                    for region in mode.to_storage.data.keys():
                        if storage.id in mode.to_storage.data[region].keys():
                            techs_to_storage.append(storage.id)
                if mode.from_storage is not None:
                    for region in mode.from_storage.data.keys():
                        if storage.id in mode.from_storage.data[region].keys():
                            techs_from_storage.append(storage.id)

        if not techs_to_storage:
            raise ValueError(f"Storage '{storage.id}' has no associated to_storage technologies")

        if not techs_from_storage:
            raise ValueError(f"Storage '{storage.id}' has no associated from_storage technologies")

    return values


def reserve_margin_fully_defined(values):
    """
    Check that reserve margin is fully defined
    """

    # Check if any reserve_margin values are not 1 (i.e. the default value)
    if any(
        value != 1
        for year_values in values.reserve_margin.data.values()
        for value in year_values.values()
    ):
        if all(
            technology.include_in_joint_reserve_margin is None for technology in values.technologies
        ):
            raise ValueError(
                "If defining reserve_margin, reserve_margin_tag_technology must be defined on at "
                "least one technology"
            )
        if all(
            commodity.include_in_joint_reserve_margin is None for commodity in values.commodities
        ):
            raise ValueError(
                "If defining reserve_margin, reserve_margin_tag_commodity must be defined on at "
                "least one commodity"
            )

    return values


def discount_rate_as_decimals(values):
    """
    Check that discount rates are in decimals
    """

    if values.discount_rate is not None:
        df = pd.json_normalize(values.discount_rate.data).iloc[:, -1]
        assert (df.abs() < 1).all(), "discount_rate should take decimal values"
    if values.cost_of_capital is not None:
        df = pd.json_normalize(values.cost_of_capital.data).iloc[:, -1]
        assert (df.abs() < 1).all(), "cost_of_capital should take decimal values"
    if values.cost_of_capital_storage is not None:
        df = pd.json_normalize(values.cost_of_capital_storage.data).iloc[:, -1]
        assert (df.abs() < 1).all(), "cost_of_capital_storage should take decimal values"

    return values
