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


def check_capacity_to_meet_demand(values):
    """
    For each commodity, check there is enough allowed capacity to meet demands
    (based on techs that directly produce the final demand)
    """
    # TODO:

    # Possibly identify the branches of technology/commodity which lead to the final demand,
    # then for every possible route, find the maximum allowed production,
    # then check the sum of each route meets demand

    # Constraints
    # activity upper limit, yearly, model period
    # emission limit

    # Identify final demands
    final_demands = []
    for commodity in values["commodities"]:
        if commodity.demand_annual is not None or commodity.accumulated_demand is not None:
            final_demands.append(commodity.id)
    """
    # Define each possible route for each final demand
    route = {"ELEC":{"TECH1":{"ratio1":"TECH3"},
                     "TECH2":{"ratio2":["TECH4",
                                       "TECH5"]}}}

    route = ["ELEC", "TECH1", "FUEL2", "TECH3"]
    # Calculate maximum possible production from each route
    routes_and_demands = {"ROUTE1":100.
                          "ROUTE2":200}


    for demand in final_demands:
        for technology in values["technologies"]:
            if technology.output_activity_ratio is not None:
                None
    """
    return values
