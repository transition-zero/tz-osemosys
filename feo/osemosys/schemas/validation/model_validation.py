def check_tech_producing_commodity(values):
    """
    For each commodity, check there is a technology which produces it
    """
    for commodity in values["commodities"]:
        technology_missing = True
        for technology in values["technologies"]:
            if technology_missing and technology.output_activity_ratio is not None:
                for region in technology.output_activity_ratio.data.keys():
                    if commodity.id in technology.output_activity_ratio.data[region].keys():
                        technology_missing = False
        if technology_missing:
            raise ValueError(f"Commodity '{commodity.id}' is not an output of any technology")

    return values


def check_tech_producing_impact(values):
    """
    For each impact, check there is a technology which produces it
    """
    for impact in values["impacts"]:
        technology_missing = True
        for technology in values["technologies"]:
            if technology_missing and technology.emission_activity_ratio is not None:
                for region in technology.emission_activity_ratio.data.keys():
                    if impact.id in technology.emission_activity_ratio.data[region].keys():
                        technology_missing = False
        if technology_missing:
            raise ValueError(f"Impact '{impact.id}' is not an output of any technology")

    return values


def check_tech_consuming_commodity(values):
    """
    For each commodity which isn't a final demand, check it is the input of a technology
    """
    for commodity in values["commodities"]:
        if commodity.demand_annual is None and commodity.accumulated_demand is None:
            technology_missing = True
            for technology in values["technologies"]:
                if technology_missing and technology.input_activity_ratio is not None:
                    for region in technology.input_activity_ratio.data.keys():
                        if commodity.id in technology.input_activity_ratio.data[region].keys():
                            technology_missing = False
            if technology_missing:
                raise ValueError(
                    f"Commodity '{commodity.id}' is neither a final demand nor "
                    f"an input of any technology"
                )

    return values
