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
