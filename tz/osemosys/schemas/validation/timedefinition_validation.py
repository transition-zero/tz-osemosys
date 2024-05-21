from itertools import product
from typing import Any, List, Mapping

# ######################################
# Validation if timeslices are defined #
# ######################################


def get_timeslices_from_sets(values):
    """
    If timeslices are not provided, but timeslice_in_x are, get timeslices from timeslice_in_x
    """
    timeslices = values.get("timeslices")
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    timeslice_in_season = values.get("timeslice_in_season")

    if timeslices is None:
        if timeslice_in_timebracket is not None:
            timeslices = list(timeslice_in_timebracket.keys())
        elif timeslice_in_daytype is not None:
            timeslices = list(timeslice_in_daytype.keys())
        elif timeslice_in_season is not None:
            timeslices = list(timeslice_in_season.keys())

    return timeslices


def timeslice_match_timeslice_in_set(timeslices: List[str | int], values: Any):
    """
    Check that provided timeslices match keys of provided time relevant sets
    i.e. timebracket, daytype, season
    """
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    timeslice_in_season = values.get("timeslice_in_season")

    for name, timeslice_in_set in [
        ("timeslice_in_timebracket", timeslice_in_timebracket),
        ("timeslice_in_daytype", timeslice_in_daytype),
        ("timeslice_in_season", timeslice_in_season),
    ]:
        if timeslices is not None and timeslice_in_set is not None:
            if set(timeslices) != set(timeslice_in_set.keys()):
                raise ValueError(f"provided 'timeslices' do not match keys of '{name}'")

    return values


def maybe_get_parts_from_timeslice_mappings(timeslices, values):
    """
    either get or validate that timeslice_in_x match keys of corresponding set
    """

    def validate_parts(part_list, timeslice_mapping, part_name, mapping_name):
        if timeslice_mapping is not None:
            if part_list is not None:
                # verify keys match
                if set(part_list) != set(timeslice_mapping.values()):
                    raise ValueError(f"provided '{mapping_name}' keys do not match '{part_name}'")
            else:
                # get part_list from timeslice_mapping
                part_list = list(timeslice_mapping.values())
                return part_list, timeslice_mapping
        else:
            if part_list is not None:
                raise ValueError(
                    f"""Provided '{part_name}' have no mapping to 'timeslices'.
                        Provide '{mapping_name}'.
                    """
                )

        return part_list, timeslice_mapping

    timeslice_in_season, timeslice_in_timebracket, timeslice_in_daytype = (
        values.get("timeslice_in_season"),
        values.get("timeslice_in_timebracket"),
        values.get("timeslice_in_daytype"),
    )

    daily_time_brackets, day_types, seasons = (
        values.get("daily_time_brackets"),
        values.get("day_types"),
        values.get("seasons"),
    )

    daily_time_brackets, timeslice_in_timebracket = validate_parts(
        daily_time_brackets,
        timeslice_in_timebracket,
        "daily_time_brackets",
        "timeslice_in_timebracket",
    )
    day_types, timeslice_in_daytype = validate_parts(
        day_types, timeslice_in_daytype, "day_types", "timeslice_in_daytype"
    )
    seasons, timeslice_in_season = validate_parts(
        seasons, timeslice_in_season, "seasons", "timeslice_in_season"
    )

    return (
        seasons,
        day_types,
        daily_time_brackets,
        timeslice_in_season,
        timeslice_in_daytype,
        timeslice_in_timebracket,
    )


def validate_parts_from_splits(timeslices, day_types, time_brackets, values):
    year_split, days_in_day_type, day_split = (
        values.get("year_split"),
        values.get("days_in_day_type"),
        values.get("day_split"),
    )

    def _maybe_check_keys_or_equal(
        split: Mapping | None, part_list: List[str | int], name: str, eq_one: bool
    ):
        if split is not None:
            if part_list is not None:
                # validate keys match
                if {str(item) for item in set(split.keys())} != set(part_list):
                    raise ValueError(f"provided '{name}_split' keys do not match '{name}'")
                return split
            else:
                raise ValueError(
                    f"Provided '{name}_split' have no ordered set '{name}' - provide set '{name}'."
                )
        # create an equal split
        if part_list is not None:
            if eq_one:
                return {p: 1 / len(part_list) for p in part_list}
            else:
                return {p: 1 for p in part_list}
        else:
            return None

    year_split = _maybe_check_keys_or_equal(year_split, timeslices, "seasons", True)
    days_in_day_type = _maybe_check_keys_or_equal(days_in_day_type, day_types, "day_types", False)
    day_split = _maybe_check_keys_or_equal(day_split, time_brackets, "daily_time_brackets", True)

    return year_split, days_in_day_type, day_split


def validate_adjacency_keys(
    adj: Mapping,
    timeslices: List[str],
    years: List[int],
    seasons: List[str] | None,
    day_types: List[str] | None,
    time_brackets: List[str] | None,
):
    if len(timeslices) > 1 and (
        set(list(adj["timeslices"].keys()) + list(adj["timeslices"].values())) != set(timeslices)
    ):
        raise ValueError("provided 'timeslices' do not match keys or values of 'adj.timeslices'")
    if {int(yr) for yr in list(adj["years"].keys()) + list(adj["years"].values())} != set(years):
        raise ValueError("provided 'years' do not match keys or values of 'adj.years'")
    if seasons is not None and "seasons" in adj.keys():
        if len(seasons) > 1:
            if set(list(adj["seasons"].keys()) + list(adj["seasons"].values())) != set(seasons):
                raise ValueError("provided 'seasons' do not match keys or values of 'adj.seasons'")
        else:
            if adj["seasons"] != {}:
                raise ValueError(
                    f"Adjacency provided for seasons, but only one season {seasons} is defined."
                )
    elif seasons is not None or adj.get("seasons"):
        raise ValueError("seasons provided without adjacency.")
    if day_types is not None and "day_types" in adj.keys():
        if len(day_types) > 1:
            if set(list(adj["day_types"].keys()) + list(adj["day_types"].values())) != set(
                day_types
            ):
                raise ValueError(
                    "provided 'day_types' do not match keys or values of 'adj.day_types'"
                )
        else:
            if adj["day_types"] != {}:
                raise ValueError(
                    f"Adjacency provided for day_types, but only one day_type {day_types} is defined."  # NOQA E501
                )
    elif day_types is not None or adj.get("day_types"):
        raise ValueError("day_types provided without adjacency")
    if time_brackets is not None and "time_brackets" in adj.keys():
        if len(time_brackets) > 1:
            if set(list(adj["time_brackets"].keys()) + list(adj["time_brackets"].values())) != set(
                time_brackets
            ):
                raise ValueError(
                    "provided 'time_brackets' do not match keys or values of 'adj.time_brackets'"
                )
        else:
            if adj["time_brackets"] != {}:
                raise ValueError(
                    f"Adjacency provided for time_brackets, but only one time_bracket {time_brackets} is defined."  # NOQA E501
                )
    elif time_brackets is not None or adj.get("time_brackets"):
        raise ValueError("time_brackets provided without adjacency")


def validate_adjacency_fullyconstrained(
    timeslices: List[str | int],
    timeslice_in_season: List[str | int] | None,
    timeslice_in_daytype: List[str | int] | None,
    timeslice_in_timebracket: List[str | int] | None,
):
    # if no mappings provided, return directly
    if all(
        [
            (timeslice_in_season is None),
            (timeslice_in_daytype is None),
            (timeslice_in_timebracket is None),
        ]
    ):
        return True
    # get set coverage of each timeslice_mapping
    # sets must be unique for each timeslice
    timeslice_sets = {ts: [] for ts in timeslices}
    if timeslice_in_season is not None:
        for k, v in timeslice_in_season.items():
            timeslice_sets[k].append(v)
    if timeslice_in_daytype is not None:
        for k, v in timeslice_in_daytype.items():
            timeslice_sets[k].append(v)
    if timeslice_in_timebracket is not None:
        for k, v in timeslice_in_timebracket.items():
            timeslice_sets[k].append(v)

    if len({tuple(v) for v in timeslice_sets.values()}) == len(timeslices):
        # set coverage is unique for each timeslice
        return True
    else:
        raise ValueError(
            """
            Timeslice mappings do not create unique ordering for timeslices.
            Specify further mappings to create a unique order for timeslices
            - or provide the adjacency matrix directly for non-unique mapping."""
        )


def build_adjacency(
    years: List[int],
    timeslices: List[int | str],
    timeslice_in_season: Mapping | None,
    timeslice_in_daytype: Mapping | None,
    timeslice_in_timebracket: Mapping | None,
    seasons: List[int | str] | None,
    day_types: List[int | str] | None,
    time_brackets: List[int | str] | None,
):
    if any([seasons, day_types, time_brackets]):
        product_slices = []
        if seasons:
            product_slices.append(seasons)
        if day_types:
            product_slices.append(day_types)
        if time_brackets:
            product_slices.append(time_brackets)

        indices = product(*product_slices)

        timeslice_sets = {ts: [] for ts in timeslices}
        if timeslice_in_season is not None:
            for k, v in timeslice_in_season.items():
                timeslice_sets[k].append(v)
        if timeslice_in_daytype is not None:
            for k, v in timeslice_in_daytype.items():
                timeslice_sets[k].append(v)
        if timeslice_in_timebracket is not None:
            for k, v in timeslice_in_timebracket.items():
                timeslice_sets[k].append(v)

        timeslice_sets = {tuple(v): k for k, v in timeslice_sets.items()}

        ordered_timeslices = [timeslice_sets[idx] for idx in indices]

    else:
        ordered_timeslices = timeslices

    return dict(
        years=dict(zip(sorted(years)[:-1], sorted(years)[1:])),
        timeslices=dict(zip(sorted(ordered_timeslices)[:-1], sorted(ordered_timeslices)[1:])),
        seasons=dict(zip(map(str, seasons[:-1]), map(str, seasons[1:]))) if seasons else None,
        day_types=(
            dict(zip(map(str, day_types[:-1]), map(str, day_types[1:]))) if day_types else None
        ),
        time_brackets=(
            dict(zip(map(str, time_brackets[:-1]), map(str, time_brackets[1:])))
            if time_brackets
            else None
        ),
    )


def time_adj_to_list(adj_dict: dict):
    """
    Convert a time adjacency dict to a chronologically ordered list
    """
    chronological_list = []
    # Add first item
    chronological_list.append(
        [item for item in adj_dict.keys() if item not in adj_dict.values()][0]
    )
    # iteratively add remaining items
    add_to_list = True
    while add_to_list:
        chronological_list.append(adj_dict[chronological_list[-1]])
        if chronological_list[-1] not in adj_dict.keys():
            add_to_list = False

    return chronological_list


# ##########################################
# Validation if timeslices are not defined #
# ##########################################


def build_timeslices_from_parts(seasons, day_types=None, time_brackets=None):
    """
    If timeslices are not provided, but parts are, get timeslices from parts
    """

    product_slices = []
    if seasons:
        product_slices.append(seasons)
    if day_types:
        product_slices.append(day_types)
    if time_brackets:
        product_slices.append(time_brackets)

    return ["-".join(timeslice) for timeslice in product(*product_slices)]
