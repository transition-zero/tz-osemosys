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


def check_able_to_meet_demands(values):
    """
    For each commodity, check there is enough allowed capacity and allowed activity to meet demands
    (for technologies that directly produce the final demand)
    """

    # Constraints on technologies:
    #   activity upper limit, annual and model period
    #   capacity limit
    #   emission limit

    # Identify final demands
    final_demands = []
    for commodity in values["commodities"]:
        if commodity.demand_annual is not None or commodity.accumulated_demand is not None:
            final_demands.append(commodity.id)

    for commodity in values["commodities"]:
        # #########################
        # Specified annual demand #
        # #########################

        if commodity.demand_annual is not None:
            # Do checks per region for which demand is specified
            for region in commodity.demand_annual.data.keys():
                # Identify technologies which produce the demand
                technologies_producing_demand = []
                technology_names = []
                for technology in values["technologies"]:
                    if technology.output_activity_ratio is not None:
                        if region in technology.output_activity_ratio.data.keys():
                            if commodity.id in technology.output_activity_ratio.data[region].keys():
                                technologies_producing_demand.append(technology)
                                technology_names.append(technology.id)

                # Check demand can be satisfied in each year
                for year in values["time_definition"].years:
                    # Get demand in each timeslice
                    total_demand = commodity.demand_annual.data[region][str(year)]
                    demand_per_timeslice = {}
                    for timeslice, demand_per_year in commodity.demand_profile.data[region].items():
                        demand_per_timeslice[timeslice] = demand_per_year[str(year)] * total_demand

                    # Caclulate total possible production per timeslice
                    total_production_limit_ts = {
                        key: 0 for key in values["time_definition"].timeslices
                    }
                    for technology in technologies_producing_demand:
                        # Find mode of operation with highest output activity ratio (OAR)
                        mode_max_oar = "1"
                        for mode in technology.output_activity_ratio.data[region][
                            commodity.id
                        ].keys():
                            try:
                                if (
                                    technology.output_activity_ratio.data[region][commodity.id][
                                        mode
                                    ][str(year)]
                                    > technology.output_activity_ratio.data[region][commodity.id][
                                        mode_max_oar
                                    ][str(year)]
                                ):
                                    mode_max_oar = mode
                            except KeyError:
                                pass

                        # Calculate limit on production from activity limit
                        if technology.activity_annual_max is not None:
                            try:
                                activity_limit = technology.activity_annual_max.data[region][
                                    str(year)
                                ]
                                # Calculate maximum possible production given activity limit
                                # prod_limit = activity_limit * OAR
                                prod_limit_activity = (
                                    activity_limit
                                    * technology.output_activity_ratio.data[region][commodity.id][
                                        mode_max_oar
                                    ][str(year)]
                                )
                                # Assume all production could take place in any timeslice
                                prod_limit_activity_per_ts = {
                                    key: prod_limit_activity
                                    for key in values["time_definition"].timeslices
                                }
                            except KeyError:
                                prod_limit_activity_per_ts = None
                        else:
                            prod_limit_activity_per_ts = None

                        # Calculate limit on production from capacity limit
                        if technology.capacity_gross_max is not None:
                            try:
                                capacity_limit = technology.capacity_gross_max.data[region][
                                    str(year)
                                ]
                                # Calculate maximum possible production given capacity limit
                                # prod_limit = capacity_limit * cap_to_act_ratio * OAR
                                prod_limit_capacity = (
                                    capacity_limit
                                    * technology.capacity_activity_unit_ratio.data[region]
                                    * technology.output_activity_ratio.data[region][commodity.id][
                                        mode_max_oar
                                    ][str(year)]
                                )

                                # Account for capacity factors
                                if technology.capacity_factor is not None:
                                    try:
                                        # production_by_ts = production_limit * capacity_factor
                                        prod_limit_capacity_per_ts = {
                                            key: prod_limit_capacity
                                            * technology.capacity_factor[region][technology.id][
                                                key
                                            ][year]
                                            for key in values["time_definition"].timeslices
                                        }
                                    except KeyError:
                                        # Assign equal production by timeslice
                                        prod_limit_capacity_per_ts = {
                                            key: prod_limit_capacity
                                            / len(values["time_definition"].timeslices)
                                            for key in values["time_definition"].timeslices
                                        }
                                else:
                                    # Assign equal production by timeslice
                                    prod_limit_capacity_per_ts = {
                                        key: prod_limit_capacity
                                        / len(values["time_definition"].timeslices)
                                        for key in values["time_definition"].timeslices
                                    }

                                # Account for availibility factors
                                if technology.availability_factor is not None:
                                    try:
                                        availability_factor = technology.availability_factor.data[
                                            region
                                        ][technology.id][year]
                                        prod_limit_capacity_per_ts = {
                                            key: value * availability_factor
                                            for key, value in prod_limit_capacity_per_ts.items()
                                        }
                                    except KeyError:
                                        pass

                            except KeyError:
                                prod_limit_capacity_per_ts = None
                        else:
                            prod_limit_capacity_per_ts = None

                        # Add limits to total possible production across all technologies
                        if (
                            prod_limit_activity_per_ts is None
                            and prod_limit_capacity_per_ts is None
                        ):
                            # If any technology is completely unconstrained, there is no production
                            # limit for the corresponding commodity
                            total_production_limit_ts = None
                        else:
                            if total_production_limit_ts is not None:
                                for timeslice in total_production_limit_ts.keys():
                                    if (
                                        prod_limit_activity_per_ts is not None
                                        and prod_limit_capacity_per_ts is not None
                                    ):
                                        maximum_production = min(
                                            prod_limit_activity_per_ts[timeslice],
                                            prod_limit_capacity_per_ts[timeslice],
                                        )
                                    elif (
                                        prod_limit_activity_per_ts is not None
                                        and prod_limit_capacity_per_ts is None
                                    ):
                                        maximum_production = prod_limit_activity_per_ts[timeslice]
                                    elif (
                                        prod_limit_activity_per_ts is None
                                        and prod_limit_capacity_per_ts is not None
                                    ):
                                        maximum_production = prod_limit_capacity_per_ts[timeslice]

                                    # Add technology specific allowable production to total
                                    # allowable production for the given commodity
                                    total_production_limit_ts[timeslice] = (
                                        total_production_limit_ts[timeslice] + maximum_production
                                    )

                    # Check demands can be met for each timeslice
                    if total_production_limit_ts is not None:
                        timeslices_insufficient_supply = []
                        for timeslice in values["time_definition"].timeslices:
                            if (
                                total_production_limit_ts[timeslice]
                                < demand_per_timeslice[timeslice]
                            ):
                                timeslices_insufficient_supply.append(timeslice)
                        if timeslices_insufficient_supply:
                            raise ValueError(
                                f"Specified Annual Demand (demand_annual) for commodity "
                                f"'{commodity.id}' in year '{year}' and region '{region}' cannot "
                                f"be met for timeslice(s): {timeslices_insufficient_supply}, "
                                f"either the activity or capacity constraints on the technologies "
                                f"producing '{commodity.id}' are too restrictive: "
                                f"{technology_names}"
                            )

        # ###########################
        # Accumulated annual demand #
        # ###########################

        # TODO:
        if commodity.accumulated_demand is not None:
            pass

    return values
