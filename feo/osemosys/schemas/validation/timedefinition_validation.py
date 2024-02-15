from itertools import product
from typing import Any, List, Mapping

import numpy as np
import pandas as pd

from feo.osemosys.schemas.base import OSeMOSYSData
from feo.osemosys.utils import flatten, group_to_json, json_dict_to_dataframe, makehash

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


def validate_parts_from_splits(seasons, day_types, time_brackets, values):
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
                if set(split.keys()) != set(part_list):
                    raise ValueError(f"provided '{name}_split' keys do not match '{name}'")
            else:
                raise ValueError(
                    "Provided '{name}_split' have no ordered set '{name}' - provide set '{name}'."
                )
        # create an equal split
        if part_list is not None:
            if eq_one:
                return {p: 1 / len(part_list) for p in part_list}
            else:
                return {p: 1 for p in part_list}
        else:
            return None

    year_split = _maybe_check_keys_or_equal(year_split, seasons, "seasons", True)
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
    print("ADJ", adj)
    print("timselices", timeslices)
    print(set(adj["timeslices"].keys()), set(timeslices))
    print(set(adj["timeslices"].values()), set(timeslices))
    print(set(sorted(list(adj["years"].keys()) + list(adj["years"].values()))))
    print(set(sorted(years)))

    if set(list(adj["timeslices"].keys()) + list(adj["timeslices"].values())) != set(timeslices):
        raise ValueError("provided 'timeslices' do not match keys or values of 'adj.timeslices'")
    if set(list(adj["years"].keys()) + list(adj["years"].values())) != set(years):
        raise ValueError("provided 'years' do not match keys or values of 'adj.years'")
    if seasons is not None and "seasons" in adj.keys():
        if set(list(adj["seasons"].keys()) + list(adj["seasons"].values())) != set(seasons):
            raise ValueError("provided 'seasons' do not match keys or values of 'adj.seasons'")
    elif seasons is not None or "seasons" in adj.keys():
        raise ValueError("seasons provided without adjacency.")
    if day_types is not None and "day_types" in adj.keys():
        if set(list(adj["day_types"].keys()) + list(adj["day_types"].values())) != set(day_types):
            raise ValueError("provided 'day_types' do not match keys or values of 'adj.day_types'")
    elif day_types is not None or "day_types" in adj.keys():
        raise ValueError("day_types provided without adjacency")
    if time_brackets is not None and "time_brackets" in adj.keys():
        if set(list(adj["time_brackets"].keys()) + list(adj["time_brackets"].values())) != set(
            time_brackets
        ):
            raise ValueError(
                "provided 'time_brackets' do not match keys or values of 'adj.time_brackets'"
            )
    elif time_brackets is not None or "time_brackets" in adj.keys():
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
        seasons=dict(zip(sorted(seasons)[:-1], sorted(seasons)[1:])) if seasons else None,
        day_types=dict(zip(sorted(day_types)[:-1], sorted(day_types)[1:])) if day_types else None,
        time_brackets=dict(zip(sorted(time_brackets)[:-1], sorted(time_brackets)[1:]))
        if time_brackets
        else None,
    )


# def construct_timebracket(values):
#     """
#     If timeslices defined, but daily_time_brackets nor timeslice_in_timebracket is,
#     construct them from timeslices, assuming a single daily_time_brackets
#     """
#     timeslices = values.get("timeslices")
#     timeslice_in_timebracket = values.get("timeslice_in_timebracket")
#     daily_time_brackets = values.get("daily_time_brackets")
#     if timeslices is not None:
#         if daily_time_brackets is None and timeslice_in_timebracket is None:
#             # TODO: potentially remove this osemosys global specific check and ValueError
#             for item in timeslices:
#                 if "H2" in item:
#                     raise ValueError(
#                         "More than one daily time bracket specified in timeslices, "
#                         "daily_time_brackets and timeslice_in_timebracket must be provided"
#                     )
#             # Construct daily_time_brackets assuming a single timebracket
#             values["daily_time_brackets"] = [1]
#             # Construct timeslice_in_timebracket assuming a single timebracket
#             timeslice_in_timebracket = pd.DataFrame({"TIMESLICE": timeslices})
#             timeslice_in_timebracket["DAILYTIMEBRACKET"] = 1
#             timeslice_in_timebracket["VALUE"] = 1
#             timeslice_in_timebracket = group_to_json(
#                 g=timeslice_in_timebracket,
#                 data_columns=["TIMESLICE", "DAILYTIMEBRACKET"],
#                 target_column="VALUE",
#             )
#             values["timeslice_in_timebracket"] = timeslice_in_timebracket
#     return values


# def construct_daytype(values):
#     """
#     If timeslices defined, but day_types nor timeslice_in_daytype is,
#     construct them from timeslices, assuming a single daytype
#     """
#     timeslices = values.get("timeslices")
#     timeslice_in_daytype = values.get("timeslice_in_daytype")
#     day_types = values.get("day_types")
#     if timeslices is not None:
#         if timeslice_in_daytype is None and day_types is None:
#             for item in timeslices:
#                 # TODO: this is osemosys global specific, needs to be generalised
#                 if "D2" in item:
#                     raise ValueError(
#                         "More than one day type specified in timeslices, day_types and "
#                         "timeslice_in_daytype must be provided"
#                     )
#             # Construct day_types assuming a single daytype
#             values["day_types"] = [1]
#             # Construct timeslice_in_daytype assuming a single daytype
#             timeslice_in_daytype = pd.DataFrame({"TIMESLICE": timeslices})
#             timeslice_in_daytype["DAYTYPE"] = 1
#             timeslice_in_daytype["VALUE"] = 1
#             timeslice_in_daytype = group_to_json(
#                 g=timeslice_in_daytype,
#                 data_columns=["TIMESLICE", "DAYTYPE"],
#                 target_column="VALUE",
#             )
#             values["timeslice_in_daytype"] = timeslice_in_daytype
#     return values


# def construct_season(values):
#     """
#     If timeslices defined, but day_types nor timeslice_in_daytype is,
#     construct them from timeslices, assuming a single daytype
#     """
#     timeslices = values.get("timeslices")
#     timeslice_in_season = values.get("timeslice_in_season")
#     seasons = values.get("seasons")
#     if timeslices is not None:
#         if seasons is None and timeslice_in_season is None:
#             for item in timeslices:
#                 if "S2" in item:
#                     raise ValueError(
#                         "More than one season specified in timeslices, seasons and "
#                         "timeslice_in_season must be provided"
#                     )
#             # default to a single season
#             values["seasons"] = [1]
#             timeslice_in_season = pd.DataFrame({"TIMESLICE": timeslices})
#             timeslice_in_season["SEASON"] = 1
#             timeslice_in_season["VALUE"] = 1
#             timeslice_in_season = group_to_json(
#                 g=timeslice_in_season,
#                 data_columns=["TIMESLICE", "SEASON"],
#                 target_column="VALUE",
#             )
#             values["timeslice_in_season"] = timeslice_in_season
#     return values


# ##########################################
# Validation if timeslices are not defined #
# ##########################################


def construct_daytypes_no_timeslice(values):
    """
    If timeslices not defined, construct day types if necessary
    """
    timeslices = values.get("timeslices")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    day_types = values.get("day_types")
    if timeslices is None and timeslice_in_daytype is not None:
        timeslices = timeslice_in_daytype.keys()
        if day_types is not None:
            if set(day_types) != set(
                flatten([list(v.keys()) for k, v in timeslice_in_daytype.items()])
            ):
                raise ValueError("provided 'timeslice_in_daytype' keys do not match 'day_types'")
        else:
            day_types = sorted(flatten([list(v.keys()) for k, v in timeslice_in_daytype.items()]))
    if timeslices is None and timeslice_in_daytype is None:
        if day_types is None:
            day_types = [1]
    values["daytype"] = day_types
    values["timeslices"] = timeslices
    return values


def construct_dailytimebracket_no_timeslice(values):
    """
    If timeslices not defined, construct daily_time_brackets if necessary
    """
    timeslices = values.get("timeslices")
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    daily_time_brackets = values.get("daily_time_brackets")
    if timeslices is None and timeslice_in_timebracket is not None:
        if timeslices is None:
            timeslices = timeslice_in_timebracket.keys()
        else:
            if set(timeslices) != set(timeslice_in_timebracket.keys()):
                raise ValueError(
                    "provided 'timeslice_in_timebracket' keys do not match other "
                    "timeslice joins."
                )
        if daily_time_brackets is not None:
            if set(daily_time_brackets) != set(
                flatten([list(v.keys()) for k, v in timeslice_in_timebracket.items()])
            ):
                raise ValueError(
                    "provided 'timeslice_in_timebracket' keys do not match " "'daily_time_brackets'"
                )
        else:
            daily_time_brackets = sorted(
                flatten([list(v.keys()) for k, v in timeslice_in_timebracket.items()])
            )
    if timeslices is None and timeslice_in_timebracket is None:
        if daily_time_brackets is None:
            daily_time_brackets = [1]
    values["daily_time_brackets"] = daily_time_brackets
    values["timeslices"] = timeslices
    return values


def construct_season_no_timeslice(values):
    """
    If timeslices not defined, construct seasons if necessary
    """
    timeslices = values.get("timeslices")
    timeslice_in_season = values.get("timeslice_in_season")
    seasons = values.get("seasons")

    if timeslices is None and timeslice_in_season is not None:
        if timeslices is None:
            timeslices = timeslice_in_season.keys()
        else:
            if set(timeslices) != set(timeslice_in_season.keys()):
                raise ValueError(
                    "provided 'timeslice_in_season' keys do not match other " "timeslice joins."
                )
        if seasons is not None:
            if set(seasons) != set(
                flatten([list(v.keys()) for k, v in timeslice_in_season.items()])
            ):
                raise ValueError("provided 'timeslice_in_season' keys do not match 'seasons'")
        else:
            seasons = sorted(flatten([list(v.keys()) for k, v in timeslice_in_season.items()]))
    if timeslices is None and timeslice_in_season is None:
        if seasons is None:
            seasons = [1]
    values["season"] = seasons
    values["timeslices"] = timeslices
    return values


def construct_timeslice(values):
    """
    if timeslices is _still_ None: join our time_brackets, day_types, and SEASON
    our timeslice_in_<object> constructs are also empty, let's build all
    """
    timeslices = values.get("timeslices")
    timeslice_in_season = values.get("timeslice_in_season")
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    seasons = values.get("seasons")
    daily_time_brackets = values.get("daily_time_brackets")
    day_types = values.get("day_types")

    if timeslices is None:
        timeslice_in_season, timeslice_in_daytype, timeslice_in_timebracket = (
            makehash(),
            makehash(),
            makehash(),
        )
        timeslices = []

        for season, day_type, time_bracket in product(seasons, day_types, daily_time_brackets):
            timeslices.append(f"S{season}D{day_type}H{time_bracket}")
            timeslice_in_season[f"S{season}D{day_type}H{time_bracket}"][season] = 1
            timeslice_in_daytype[f"S{season}D{day_type}H{time_bracket}"][day_type] = 1
            timeslice_in_timebracket[f"S{season}D{day_type}H{time_bracket}"][time_bracket] = 1

        values["timeslices"] = timeslices
        values["timeslice_in_season"] = timeslice_in_season
        values["timeslice_in_timebracket"] = timeslice_in_timebracket
        values["timeslice_in_daytype"] = timeslice_in_daytype
    return values


# ###################################################################
# Validation/construction for year_split/day_split/days_in_day_type #
# ###################################################################


def validate_construct_year_split(values):
    """
    If year_split provided, check it's keys match those in timeslice, and that it sums to one
    Otherwise construct year_split from timeslices
    """
    year_split = values.get("year_split")
    timeslices = values.get("timeslices")
    years = values.get("years")

    if year_split is not None:
        # Check year_split keys match timeslices
        if set(year_split.keys()) != set(timeslices):
            raise ValueError("'year_split' keys do not match timeslices.")

        # Check year_split sum equals 1, within leniency
        # TODO: determine if leniency of 0.05 is acceptable
        leniency = 0.05
        year_split_df = json_dict_to_dataframe(year_split)
        year_split_df.columns = ["TIMESLICE", "YEAR", "VALUE"]
        assert np.allclose(
            year_split_df.groupby(["YEAR"])["VALUE"].sum(), 1, atol=leniency
        ), f"year_split must sum to one (within {leniency}) for all years"

    # Construct year_split if not provided
    else:
        # Assume each timeslice of same length
        year_split_length = 1 / len(timeslices)

        # Construct data
        year_split_df = pd.DataFrame(
            {
                "TIMESLICE": pd.Series(dtype="object"),
                "YEAR": pd.Series(dtype="int32"),
                "VALUE": pd.Series(dtype="float64"),
            }
        )

        for timeslice in timeslices:
            year_split_df = pd.concat(
                [
                    year_split_df,
                    pd.DataFrame(
                        {
                            "TIMESLICE": timeslice,
                            "YEAR": years,
                            "VALUE": year_split_length,
                        }
                    ),
                ]
            )
        year_split = group_to_json(
            g=year_split_df,
            data_columns=["TIMESLICE", "YEAR"],
            target_column="VALUE",
        )
        values["year_split"] = OSeMOSYSData(data=year_split)

    return values


def validate_construct_day_split(values):
    """
    Check day_split keys match those in daily_time_brackets
    If day_split not provided, construct it from daily_time_brackets
    """
    day_split = values.get("day_split")
    daily_time_brackets = values.get("daily_time_brackets")
    years = values.get("years")

    if day_split is not None:
        if set(day_split.keys()) != set(daily_time_brackets):
            raise ValueError("'day_split' keys do not match daily_time_brackets.")
    else:
        # Assume all daily ticket brackets are of equal length
        day_split_length = ((1 / len(daily_time_brackets)) * 24) / (365 * 24)

        # Construct data
        day_split_df = pd.DataFrame(
            {
                "DAILYTIMEBRACKET": pd.Series(dtype="object"),
                "YEAR": pd.Series(dtype="int32"),
                "VALUE": pd.Series(dtype="float64"),
            }
        )
        for bracket in daily_time_brackets:
            day_split_df = pd.concat(
                [
                    day_split_df,
                    pd.DataFrame(
                        {
                            "DAILYTIMEBRACKET": bracket,
                            "YEAR": years,
                            "VALUE": day_split_length,
                        }
                    ),
                ]
            )
        day_split = group_to_json(
            g=day_split_df,
            data_columns=["DAILYTIMEBRACKET", "YEAR"],
            target_column="VALUE",
        )
        values["day_split"] = day_split

    return values


def validate_construct_days_in_day_type(values):
    """
    If provided, check days_in_day_type keys match day_types
    Otherwise construct days_in_day_type
    """
    days_in_day_type = values.get("days_in_day_type")
    seasons = values.get("seasons")
    years = values.get("years")
    day_types = values.get("day_types")

    if days_in_day_type is not None:
        # Get daytypes from 2nd level of nested keys
        daytype_keys = []
        for _level1_key, level2_dict in days_in_day_type.items():
            for level2_key in level2_dict:
                daytype_keys.append(level2_key)
        if set(daytype_keys) != set(day_types):
            raise ValueError("'days_in_day_type' keys do not match day_types.")
    else:
        if day_types is not None:
            if len(day_types) > 1:
                raise ValueError(
                    "days_in_day_type must be provided if providing more than one daytype"
                )
        else:
            day_types = [1]
            values["day_types"] = day_types

        days_in_day_type_df = pd.DataFrame(
            {
                "SEASON": pd.Series(dtype="object"),
                "DAYTYPE": pd.Series(dtype="object"),
                "YEAR": pd.Series(dtype="int32"),
                "VALUE": pd.Series(dtype="float64"),
            }
        )
        for season in seasons:
            days_in_day_type_df = pd.concat(
                [
                    days_in_day_type_df,
                    pd.DataFrame({"SEASON": season, "DAYTYPE": 1, "YEAR": years, "VALUE": 7}),
                ]
            )
        days_in_day_type = group_to_json(
            g=days_in_day_type_df,
            data_columns=["SEASON", "DAYTYPE", "YEAR"],
            target_column="VALUE",
        )
        values["days_in_day_type"] = days_in_day_type

    return values


# ###################################
# Construction of adjaceny matrices #
# ###################################


def construct_adjacency_matrices(values):
    """
    Constructs the adjaceny matrices for years, seasons, day_types, and time_brackets
    """
    years = values.get("years")
    seasons = values.get("seasons")
    day_types = values.get("day_types")
    daily_time_brackets = values.get("daily_time_brackets")
    adj = values.get("adj")
    adj_inv = values.get("adj_inv")

    if adj is None or adj_inv is None:
        year_adjacency = dict(zip(sorted(years)[:-1], sorted(years)[1:]))
        year_adjacency_inv = dict(zip(sorted(years)[1:], sorted(years)[:-1]))
        season_adjacency = dict(zip(sorted(seasons)[:-1], sorted(seasons)[1:]))
        season_adjacency_inv = dict(zip(sorted(seasons)[1:], sorted(seasons)[:-1]))
        day_type_adjacency = dict(zip(sorted(day_types)[:-1], sorted(day_types)[1:]))
        day_type_adjacency_inv = dict(zip(sorted(day_types)[1:], sorted(day_types)[:-1]))
        time_brackets_adjacency = dict(
            zip(sorted(daily_time_brackets)[:-1], sorted(daily_time_brackets)[1:])
        )
        time_brackets_adjacency_inv = dict(
            zip(sorted(daily_time_brackets)[1:], sorted(daily_time_brackets)[:-1])
        )

        adj = dict(
            years=year_adjacency,
            seasons=season_adjacency,
            day_types=day_type_adjacency,
            time_brackets=time_brackets_adjacency,
        )

        adj_inv = dict(
            years=year_adjacency_inv,
            seasons=season_adjacency_inv,
            day_types=day_type_adjacency_inv,
            time_brackets=time_brackets_adjacency_inv,
        )

        values["adj"] = adj
        values["adj_inv"] = adj_inv

    return values
