from itertools import product

import numpy as np
import pandas as pd

from feo.osemosys.schemas.base import OSeMOSYSData
from feo.osemosys.utils import flatten, group_to_json, json_dict_to_dataframe, makehash

# ######################################
# Validation if timeslices are defined #
# ######################################


def timeslice_match_timeslice_in_timebracket(values):
    """
    Check that provided timeslices match keys of provided timeslice_in_timebracket
    """
    timeslices = values.get("timeslices")
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")

    if timeslices is not None and timeslice_in_timebracket is not None:
        if set(timeslices) != set(timeslice_in_timebracket.keys()):
            raise ValueError(
                "provided 'timeslices' do not match keys of 'timeslice_in_timebracket'"
            )
    return values


def timeslice_in_timebracket_match_daily_time_brackets(values):
    """
    Check that provided timeslice_in_timebracket match keys of provided daily_time_brackets
    """
    timeslices = values.get("timeslices")
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    daily_time_brackets = values.get("daily_time_brackets")

    if timeslices is not None and timeslice_in_timebracket is not None:
        if daily_time_brackets is not None:
            if set(daily_time_brackets) != set(
                flatten([list(v.keys()) for k, v in timeslice_in_timebracket.items()])
            ):
                raise ValueError(
                    "provided 'timeslice_in_timebracket' keys do not match " "'daily_time_brackets'"
                )
    return values


def timeslice_in_timebracket_provided(values):
    """
    Check timeslice_in_timebracket is provided, if both 'timeslices' and 'time_brackets' are
    """
    timeslices = values.get("timeslices")
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    daily_time_brackets = values.get("daily_time_brackets")
    if timeslices is not None and daily_time_brackets is not None:
        if timeslice_in_timebracket is None:
            raise ValueError(
                "if providing 'timeslices' and 'time_brackets', the joining "
                "'timeslice_in_timebracket' must be provided"
            )
    return values


def construct_timebracket(values):
    """
    If timeslices defined, but daily_time_brackets nor timeslice_in_timebracket is,
    construct them from timeslices, assuming a single daily_time_brackets
    """
    timeslices = values.get("timeslices")
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    daily_time_brackets = values.get("daily_time_brackets")
    if timeslices is not None:
        if daily_time_brackets is None and timeslice_in_timebracket is None:
            # TODO: potentially remove this osemosys global specific check and ValueError
            for item in timeslices:
                if "H2" in item:
                    raise ValueError(
                        "More than one daily time bracket specified in timeslices, "
                        "daily_time_brackets and timeslice_in_timebracket must be provided"
                    )
            # Construct daily_time_brackets assuming a single timebracket
            values["daily_time_brackets"] = [1]
            # Construct timeslice_in_timebracket assuming a single timebracket
            timeslice_in_timebracket = pd.DataFrame({"TIMESLICE": timeslices})
            timeslice_in_timebracket["DAILYTIMEBRACKET"] = 1
            timeslice_in_timebracket["VALUE"] = 1
            timeslice_in_timebracket = group_to_json(
                g=timeslice_in_timebracket,
                data_columns=["TIMESLICE", "DAILYTIMEBRACKET"],
                target_column="VALUE",
            )
            values["timeslice_in_timebracket"] = timeslice_in_timebracket
    return values


def timeslice_match_timeslice_in_daytype(values):
    """
    Check provided timeslices match the keys of timeslice_in_daytype
    """
    timeslices = values.get("timeslices")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    if timeslices is not None and timeslice_in_daytype is not None:
        if set(timeslices) != set(timeslice_in_daytype.keys()):
            raise ValueError("provided 'timeslices' do not match keys of 'timeslice_in_daytype'")
    return values


def timeslice_in_daytype_match_day_types(values):
    """
    Check provided 'timeslice_in_daytype' keys match 'day_types'
    """
    timeslices = values.get("timeslices")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    day_types = values.get("day_types")
    if timeslices is not None and timeslice_in_daytype is not None:
        if day_types is not None:
            if set(day_types) != set(
                flatten([list(v.keys()) for k, v in timeslice_in_daytype.items()])
            ):
                raise ValueError("provided 'timeslice_in_daytype' keys do not match 'day_types'")
    return values


def timeslice_in_daytype_provided(values):
    """
    Check timeslice_in_daytype is provided, if both 'timeslices' and 'day_types' are
    """
    timeslices = values.get("timeslices")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    day_types = values.get("day_types")
    if timeslices is not None and day_types is not None:
        if timeslice_in_daytype is None:
            raise ValueError(
                "if providing 'timeslices' and 'day_types', the joining "
                "'timeslice_in_daytype' must be provided"
            )
    return values


def construct_daytype(values):
    """
    If timeslices defined, but day_types nor timeslice_in_daytype is,
    construct them from timeslices, assuming a single daytype
    """
    timeslices = values.get("timeslices")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    day_types = values.get("day_types")
    if timeslices is not None:
        if timeslice_in_daytype is None and day_types is None:
            for item in timeslices:
                # TODO: this is osemosys global specific, needs to be generalised
                if "D2" in item:
                    raise ValueError(
                        "More than one day type specified in timeslices, day_types and "
                        "timeslice_in_daytype must be provided"
                    )
            # Construct day_types assuming a single daytype
            values["day_types"] = [1]
            # Construct timeslice_in_daytype assuming a single daytype
            timeslice_in_daytype = pd.DataFrame({"TIMESLICE": timeslices})
            timeslice_in_daytype["DAYTYPE"] = 1
            timeslice_in_daytype["VALUE"] = 1
            timeslice_in_daytype = group_to_json(
                g=timeslice_in_daytype,
                data_columns=["TIMESLICE", "DAYTYPE"],
                target_column="VALUE",
            )
            values["timeslice_in_daytype"] = timeslice_in_daytype
    return values


def timeslice_match_timeslice_in_season(values):
    """
    Check provided timeslices match the keys of timeslice_in_season
    """
    timeslices = values.get("timeslices")
    timeslice_in_season = values.get("timeslice_in_season")
    if timeslices is not None and timeslice_in_season is not None:
        if set(timeslices) != set(timeslice_in_season.keys()):
            raise ValueError("provided 'timeslices' do not match keys of 'timeslice_in_season'")
    return values


def timeslice_in_season_match_seasons(values):
    """
    Check provided 'timeslice_in_season' keys match 'season'
    """
    timeslices = values.get("timeslices")
    timeslice_in_season = values.get("timeslice_in_season")
    seasons = values.get("seasons")
    if timeslices is not None and timeslice_in_season is not None:
        if set(seasons) != set(flatten([list(v.keys()) for k, v in timeslice_in_season.items()])):
            raise ValueError("provided 'timeslice_in_season' keys do not match 'seasons'")
    return values


def timeslice_in_season_provided(values):
    """
    Check timeslice_in_season is provided, if both 'timeslices' and 'season' are
    """
    timeslices = values.get("timeslices")
    timeslice_in_season = values.get("timeslice_in_season")
    seasons = values.get("seasons")
    if timeslices is not None and seasons is not None:
        if timeslice_in_season is None:
            raise ValueError(
                "if providing 'timeslices' and 'seasons', the joining "
                "'timeslice_in_season' must be provided"
            )
    return values


def construct_season(values):
    """
    If timeslices defined, but day_types nor timeslice_in_daytype is,
    construct them from timeslices, assuming a single daytype
    """
    timeslices = values.get("timeslices")
    timeslice_in_season = values.get("timeslice_in_season")
    seasons = values.get("seasons")
    if timeslices is not None:
        if seasons is None and timeslice_in_season is None:
            for item in timeslices:
                if "S2" in item:
                    raise ValueError(
                        "More than one season specified in timeslices, seasons and "
                        "timeslice_in_season must be provided"
                    )
            # default to a single season
            values["seasons"] = [1]
            timeslice_in_season = pd.DataFrame({"TIMESLICE": timeslices})
            timeslice_in_season["SEASON"] = 1
            timeslice_in_season["VALUE"] = 1
            timeslice_in_season = group_to_json(
                g=timeslice_in_season,
                data_columns=["TIMESLICE", "SEASON"],
                target_column="VALUE",
            )
            values["timeslice_in_season"] = timeslice_in_season
    return values


def timedefinition_validation(values):
    years = values.get("years")
    seasons = values.get("seasons")
    timeslices = values.get("timeslices")
    day_types = values.get("day_types")
    daily_time_brackets = values.get("daily_time_brackets")
    values.get("mode_of_operation")
    year_split = values.get("year_split")
    day_split = values.get("day_split")
    days_in_day_type = values.get("days_in_day_type")
    timeslice_in_timebracket = values.get("timeslice_in_timebracket")
    timeslice_in_daytype = values.get("timeslice_in_daytype")
    timeslice_in_season = values.get("timeslice_in_season")
    adj = values.get("adj")
    adj_inv = values.get("adj_inv")

    # ##########################################
    # Validation if timeslices are not defined #
    # ##########################################

    # timeslices not defined
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

    if timeslices is None:
        # timeslices is _still_ None: join our time_brackets, day_types, and SEASON
        # our timeslice_in_<object> constructs are also empty, let's build all

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

    # For year_split/day_split/days_in_day_type:
    # check that they have the correct keys, or if they're None build from scratch

    # year_split
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

    # day_split
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

    # days_in_day_type
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

    values["year_split"] = OSeMOSYSData(data=year_split)
    values["day_split"] = OSeMOSYSData(data=day_split)
    values["days_in_day_type"] = OSeMOSYSData(data=days_in_day_type)
    values["timeslice_in_timebracket"] = OSeMOSYSData(data=timeslice_in_timebracket)
    values["timeslice_in_daytype"] = OSeMOSYSData(data=timeslice_in_daytype)
    values["timeslice_in_season"] = OSeMOSYSData(data=timeslice_in_season)
    values["seasons"] = seasons
    values["timeslices"] = timeslices
    values["day_types"] = day_types
    values["daily_time_brackets"] = daily_time_brackets
    values["adj"] = adj
    values["adj_inv"] = adj_inv

    return values
