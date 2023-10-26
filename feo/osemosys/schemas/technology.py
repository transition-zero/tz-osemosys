import os

import pandas as pd

from feo.osemosys.utils import *

from .base import *

# ##################
# ### TECHNOLOGY ###
# ##################


class Technology(OSeMOSYSBase):
    """
    Class to contain all information pertaining to technologies (excluding storage technologies)
    """

    # Capacity unit to activity unit conversion
    # Conversion factor relating the energy that would be produced when one unit of capacity is fully used in one year.
    capacity_activity_unit_ratio: RegionData | None

    # Capacity of one new unit of a technology
    # If specified the problem will turn into a Mixed Integer Linear Problem
    capacity_one_tech_unit: RegionYearData | None

    # Capacity factor, lifespan, availability
    availability_factor: RegionYearData | None  # Maximum time a technology can run in the whole year, as a fraction from 0 to 1
    capacity_factor: RegionYearTimeData | None
    operating_life: RegionData | None

    # financials
    capex: RegionYearData | None
    opex_fixed: RegionYearData | None
    opex_variable: RegionModeYearData | None

    # initial capacity
    residual_capacity: RegionYearData | None

    # constraints - capacity
    capacity_gross_max: RegionYearData | None  # Maximum technology capacity (installed + residual) per year
    capacity_gross_min: RegionYearData | None  # Minimum technology capacity (installed + residual) per year
    capacity_additional_max: RegionYearData | None  # Maximum technology capacity additions per year
    capacity_additional_min: RegionYearData | None  # Minimum technology capacity additions per year

    # TODO
    # Relative growth rate restrictions not currently implemented in osemosys, can be added via change in osemosys code
    # additional_capacity_max_growth_rate: RegionYearData     # growth rate (<1.)
    # additional_capacity_max_ceil: RegionYearData            # Absolute value (ceil relative to growth rate)
    # additional_capacity_max_floor: RegionYearData           # absolute value (floor relative to growth rate)
    # additional_capacity_min_growth_rate: RegionYearData     # growth rate (<1.)

    # constraints - activity
    activity_annual_max: RegionYearData | None  # Maximum technology activity per year
    activity_annual_min: RegionYearData | None  # Minimum technology activity per year
    activity_total_max: RegionData | None  # Maximum technology activity across whole modelled period
    activity_total_min: RegionData | None  # Minimum technology activity across whole modelled period

    # activity ratios & efficiency
    emission_activity_ratio: StringStringIntIntData | None  # Technology emission activity ratio by mode of operation
    input_activity_ratio: StringStringIntIntData | None  # Technology fuel input activity ratio by mode of operation
    output_activity_ratio: StringStringIntIntData | None  # Technology fuel output activity ratio by mode of operation
    to_storage: StringStringIntIntData | None  # Binary parameter linking a technology to the storage facility it charges (1 linked, 0 unlinked)
    from_storage: StringStringIntIntData | None  # Binary parameter linking a storage facility to the technology it feeds (1 linked, 0 unlinked)

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        df_technologies = pd.read_csv(os.path.join(root_dir, "TECHNOLOGY.csv"))
        pd.read_csv(os.path.join(root_dir, "MODE_OF_OPERATION.csv"))

        parser_data = [
            {
                "name": "capacity_activity_unit_ratio",
                "filepath": "CapacityToActivityUnit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION"],
            },
            {
                "name": "capacity_one_tech_unit",
                "filepath": "CapacityOfOneTechnologyUnit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "availability_factor",
                "filepath": "AvailabilityFactor.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "capacity_factor",
                "filepath": "CapacityFactor.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "TIMESLICE", "YEAR"],
            },
            {
                "name": "operating_life",
                "filepath": "OperationalLife.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION"],
            },
            {
                "name": "capex",
                "filepath": "CapitalCost.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "opex_fixed",
                "filepath": "FixedCost.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "opex_variable",
                "filepath": "VariableCost.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "MODE_OF_OPERATION", "YEAR"],
            },
            {
                "name": "residual_capacity",
                "filepath": "ResidualCapacity.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "capacity_gross_max",
                "filepath": "TotalAnnualMaxCapacity.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "capacity_gross_min",
                "filepath": "TotalAnnualMinCapacity.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "capacity_additional_max",
                "filepath": "TotalAnnualMaxCapacityInvestment.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "capacity_additional_min",
                "filepath": "TotalAnnualMinCapacityInvestment.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "activity_annual_max",
                "filepath": "TotalTechnologyAnnualActivityUpperLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "activity_annual_min",
                "filepath": "TotalTechnologyAnnualActivityLowerLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "activity_total_max",
                "filepath": "TotalTechnologyModelPeriodActivityUpperLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "activity_total_min",
                "filepath": "TotalTechnologyModelPeriodActivityLowerLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "emission_activity_ratio",
                "filepath": "EmissionActivityRatio.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "EMISSION", "MODE_OF_OPERATION", "YEAR"],
            },
            {
                "name": "input_activity_ratio",
                "filepath": "InputActivityRatio.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "FUEL", "MODE_OF_OPERATION", "YEAR"],
            },
            {
                "name": "output_activity_ratio",
                "filepath": "OutputActivityRatio.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "FUEL", "MODE_OF_OPERATION", "YEAR"],
            },
            {
                "name": "to_storage",
                "filepath": "TechnologyToStorage.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "STORAGE", "MODE_OF_OPERATION"],
            },
            {
                "name": "from_storage",
                "filepath": "TechnologyFromStorage.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "STORAGE", "MODE_OF_OPERATION"],
            },
        ]

        # Read in dataframes - Creates dict of "name":dataframe
        df_all = {}
        for parser in parser_data:
            df_all[parser["name"]] = pd.read_csv(os.path.join(root_dir, parser["filepath"]))

        # Define class instances
        technology_instances = []
        for technology in df_technologies["VALUE"].values.tolist():
            data_json_format = {}
            for parser in parser_data:
                data_json_format[parser["name"]] = (
                    group_to_json(
                        g=df_all[parser["name"]].loc[
                            df_all[parser["name"]]["TECHNOLOGY"] == technology
                        ],
                        root_column=parser["root_column"],
                        data_columns=parser["data_columns"],
                        target_column="VALUE",
                    )
                    if technology in df_all[parser["name"]]["TECHNOLOGY"].values
                    else None
                )

            technology_instances.append(
                cls(
                    id=technology,
                    long_name=None,
                    description=None,
                    capacity_activity_unit_ratio=RegionData(
                        data=data_json_format["capacity_activity_unit_ratio"]
                    )
                    if data_json_format["capacity_activity_unit_ratio"] is not None
                    else None,
                    capacity_one_tech_unit=RegionYearData(
                        data=data_json_format["capacity_one_tech_unit"]
                    )
                    if data_json_format["capacity_one_tech_unit"] is not None
                    else None,
                    availability_factor=RegionYearData(data=data_json_format["availability_factor"])
                    if data_json_format["availability_factor"] is not None
                    else None,
                    capacity_factor=RegionYearTimeData(data=data_json_format["capacity_factor"])
                    if data_json_format["capacity_factor"] is not None
                    else None,
                    operating_life=RegionData(data=data_json_format["operating_life"])
                    if data_json_format["operating_life"] is not None
                    else None,
                    capex=RegionYearData(data=data_json_format["capex"])
                    if data_json_format["capex"] is not None
                    else None,
                    opex_fixed=RegionYearData(data=data_json_format["opex_fixed"])
                    if data_json_format["opex_fixed"] is not None
                    else None,
                    opex_variable=RegionModeYearData(data=data_json_format["opex_variable"])
                    if data_json_format["opex_variable"] is not None
                    else None,
                    residual_capacity=RegionYearData(data=data_json_format["residual_capacity"])
                    if data_json_format["residual_capacity"] is not None
                    else None,
                    capacity_gross_max=RegionYearData(data=data_json_format["capacity_gross_max"])
                    if data_json_format["capacity_gross_max"] is not None
                    else None,
                    capacity_gross_min=RegionYearData(data=data_json_format["capacity_gross_min"])
                    if data_json_format["capacity_gross_min"] is not None
                    else None,
                    capacity_additional_max=RegionYearData(
                        data=data_json_format["capacity_additional_max"]
                    )
                    if data_json_format["capacity_additional_max"] is not None
                    else None,
                    capacity_additional_min=RegionYearData(
                        data=data_json_format["capacity_additional_min"]
                    )
                    if data_json_format["capacity_additional_min"] is not None
                    else None,
                    activity_annual_max=RegionYearData(data=data_json_format["activity_annual_max"])
                    if data_json_format["activity_annual_max"] is not None
                    else None,
                    activity_annual_min=RegionYearData(data=data_json_format["activity_annual_min"])
                    if data_json_format["activity_annual_min"] is not None
                    else None,
                    activity_total_max=RegionData(data=data_json_format["activity_total_max"])
                    if data_json_format["activity_total_max"] is not None
                    else None,
                    activity_total_min=RegionData(data=data_json_format["activity_total_min"])
                    if data_json_format["activity_total_min"] is not None
                    else None,
                    emission_activity_ratio=StringStringIntIntData(
                        data=data_json_format["emission_activity_ratio"]
                    )
                    if data_json_format["emission_activity_ratio"] is not None
                    else None,
                    input_activity_ratio=StringStringIntIntData(
                        data=data_json_format["input_activity_ratio"]
                    )
                    if data_json_format["input_activity_ratio"] is not None
                    else None,
                    output_activity_ratio=StringStringIntIntData(
                        data=data_json_format["output_activity_ratio"]
                    )
                    if data_json_format["output_activity_ratio"] is not None
                    else None,
                    to_storage=StringStringIntIntData(data=data_json_format["to_storage"])
                    if data_json_format["to_storage"] is not None
                    else None,
                    from_storage=StringStringIntIntData(data=data_json_format["from_storage"])
                    if data_json_format["from_storage"] is not None
                    else None,
                )
            )

        return technology_instances


class TechnologyStorage(OSeMOSYSBase):
    """
    Class to contain all information pertaining to storage technologies
    """

    capex: RegionYearData | None
    operating_life: RegionData | None
    minimum_charge: RegionYearData | None  # Lower bound to the amount of energy stored, as a fraction of the maximum, with a number reanging between 0 and 1
    initial_level: RegionData | None  # Level of storage at the beginning of first modelled year, in units of activity
    residual_capacity: RegionYearData | None
    max_discharge_rate: RegionData | None  # Maximum discharging rate for the storage, in units of activity per year
    max_charge_rate: RegionData | None  # Maximum charging rate for the storage, in units of activity per year

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        df_storage_technologies = pd.read_csv(os.path.join(root_dir, "STORAGE.csv"))

        df_capex = pd.read_csv(os.path.join(root_dir, "TechnologyFromStorage.csv"))
        df_operating_life = pd.read_csv(os.path.join(root_dir, "TechnologyFromStorage.csv"))
        df_minimum_charge = pd.read_csv(os.path.join(root_dir, "TechnologyFromStorage.csv"))
        df_initial_level = pd.read_csv(os.path.join(root_dir, "TechnologyFromStorage.csv"))
        df_residual_capacity = pd.read_csv(os.path.join(root_dir, "TechnologyFromStorage.csv"))
        df_max_discharge_rate = pd.read_csv(os.path.join(root_dir, "TechnologyFromStorage.csv"))
        df_max_charge_rate = pd.read_csv(os.path.join(root_dir, "TechnologyFromStorage.csv"))

        storage_instances = []
        for storage in df_storage_technologies["VALUE"].values.tolist():
            storage_instances.append(
                cls(
                    id=storage,
                    long_name=None,
                    description=None,
                    capex=(
                        RegionYearData(
                            data=group_to_json(
                                g=df_capex.loc[df_capex["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_capex["STORAGE"].values
                        else None
                    ),
                    operating_life=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_operating_life.loc[df_operating_life["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_operating_life["STORAGE"].values
                        else None
                    ),
                    minimum_charge=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_minimum_charge.loc[df_minimum_charge["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_minimum_charge["STORAGE"].values
                        else None
                    ),
                    initial_level=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_initial_level.loc[df_initial_level["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_initial_level["STORAGE"].values
                        else None
                    ),
                    residual_capacity=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_residual_capacity.loc[
                                    df_residual_capacity["STORAGE"] == storage
                                ],
                                root_column="STORAGE",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_residual_capacity["STORAGE"].values
                        else None
                    ),
                    max_discharge_rate=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_max_discharge_rate.loc[
                                    df_max_discharge_rate["STORAGE"] == storage
                                ],
                                root_column="STORAGE",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_max_discharge_rate["STORAGE"].values
                        else None
                    ),
                    max_charge_rate=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_max_charge_rate.loc[df_max_charge_rate["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_max_charge_rate["STORAGE"].values
                        else None
                    ),
                )
            )

        return storage_instances
