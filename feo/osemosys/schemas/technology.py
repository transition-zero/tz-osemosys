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
    operating_life: StringInt | None

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

    # Renewable technology tag
    RETagTechnology: RegionTechnologyYearData | None # Binary parameter indicating technologies that can contribute to renewable targets (1 RE, 0 non-RE)

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        df_technologies = pd.read_csv(os.path.join(root_dir, "TECHNOLOGY.csv"))

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
                "data_columns": ["REGION"],
            },
            {
                "name": "activity_total_max",
                "filepath": "TotalTechnologyModelPeriodActivityUpperLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION"],
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
            {
                "name": "RETagTechnology",
                "filepath": "RETagTechnology.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR", "VALUE"],
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
                    operating_life=StringInt(data=data_json_format["operating_life"])
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
                    RETagTechnology=RegionTechnologyYearData(data=data_json_format["RETagTechnology"])
                    if data_json_format["RETagTechnology"] is not None
                    else None,
                )
            )

        return technology_instances
    

    def to_otoole_csv(self, comparison_directory) -> "cls":

        # capacity_activity_unit_ratio
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capacity_activity_unit_ratio, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="CapacityToActivityUnit.csv")
        # capacity_one_tech_unit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capacity_one_tech_unit, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="CapacityOfOneTechnologyUnit.csv")
        # availability_factor
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.availability_factor, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="AvailabilityFactor.csv")
        # capacity_factor
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capacity_factor, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "TIMESLICE", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="CapacityFactor.csv")
        # operating_life
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.operating_life, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="OperationalLife.csv")
        # capex
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capex, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="CapitalCost.csv")
        # opex_fixed
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.opex_fixed, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="FixedCost.csv")
        # opex_variable
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.opex_variable, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="VariableCost.csv")
        # residual_capacity
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.residual_capacity, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="ResidualCapacity.csv")
        # capacity_gross_max
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capacity_gross_max, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalAnnualMaxCapacity.csv")
        # capacity_gross_min
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capacity_gross_min, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalAnnualMinCapacity.csv")
        # capacity_additional_max
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capacity_additional_max, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalAnnualMaxCapacityInvestment.csv")
        # capacity_additional_min
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capacity_additional_min, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalAnnualMinCapacityInvestment.csv")
        # activity_annual_max
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.activity_annual_max, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalTechnologyAnnualActivityUpperLimit.csv")
        # activity_annual_min
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.activity_annual_min, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalTechnologyAnnualActivityLowerLimit.csv")
        # activity_total_max
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.activity_total_max, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalTechnologyModelPeriodActivityUpperLimit.csv")
        # activity_total_min
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.activity_total_min, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalTechnologyModelPeriodActivityLowerLimit.csv")
        # emission_activity_ratio
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.emission_activity_ratio, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "EMISSION", "MODE_OF_OPERATION", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="EmissionActivityRatio.csv")
        # input_activity_ratio
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.input_activity_ratio, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="InputActivityRatio.csv")
        # output_activity_ratio
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.output_activity_ratio, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="OutputActivityRatio.csv")
        # to_storage
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.to_storage, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TechnologyToStorage.csv")
        # from_storage
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.from_storage, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TechnologyFromStorage.csv")
        # RETagTechnology
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.RETagTechnology, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="RETagTechnology.csv")
        
        
        
        

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

        df_capex = pd.read_csv(os.path.join(root_dir, "CapitalCostStorage.csv"))
        df_operating_life = pd.read_csv(os.path.join(root_dir, "OperationalLifeStorage.csv"))
        df_minimum_charge = pd.read_csv(os.path.join(root_dir, "MinStorageCharge.csv"))
        df_initial_level = pd.read_csv(os.path.join(root_dir, "StorageLevelStart.csv"))
        df_residual_capacity = pd.read_csv(os.path.join(root_dir, "ResidualStorageCapacity.csv"))
        df_max_discharge_rate = pd.read_csv(os.path.join(root_dir, "StorageMaxDischargeRate.csv"))
        df_max_charge_rate = pd.read_csv(os.path.join(root_dir, "StorageMaxChargeRate.csv"))

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
    
    def to_otoole_csv(self, comparison_directory) -> "cls":

        # capex
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.capex, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "YEAR", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="CapitalCostStorage.csv")
        # operating_life
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.operating_life, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="OperationalLifeStorage.csv")
        # minimum_charge
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.minimum_charge, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "YEAR", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="MinStorageCharge.csv")
        # initial_level
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.initial_level, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="StorageLevelStart.csv")
        # residual_capacity
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.residual_capacity, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "YEAR", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="ResidualStorageCapacity.csv")
        # max_discharge_rate
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.max_discharge_rate, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="StorageMaxDischargeRate.csv")
        # max_charge_rate
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.max_charge_rate, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="StorageMaxChargeRate.csv")

    @classmethod  
    def to_empty_csv(cls, comparison_directory):
        """
        If no storage technologies present, write empty CSVs in the otoole format
        """
        pd.DataFrame(columns=["VALUE"]).to_csv(os.path.join(comparison_directory, "STORAGE.csv"), index=False)
        pd.DataFrame(columns=["REGION", "STORAGE", "YEAR", "VALUE"]).to_csv(os.path.join(comparison_directory, "CapitalCostStorage.csv"), index=False)
        pd.DataFrame(columns=["REGION", "STORAGE", "VALUE"]).to_csv(os.path.join(comparison_directory, "OperationalLifeStorage.csv"), index=False)
        pd.DataFrame(columns=["REGION", "STORAGE", "YEAR", "VALUE"]).to_csv(os.path.join(comparison_directory, "MinStorageCharge.csv"), index=False)
        pd.DataFrame(columns=["REGION", "STORAGE", "VALUE"]).to_csv(os.path.join(comparison_directory, "StorageLevelStart.csv"), index=False)
        pd.DataFrame(columns=["REGION", "STORAGE", "YEAR", "VALUE"]).to_csv(os.path.join(comparison_directory, "ResidualStorageCapacity.csv"), index=False)
        pd.DataFrame(columns=["REGION", "STORAGE", "VALUE"]).to_csv(os.path.join(comparison_directory, "StorageMaxDischargeRate.csv"), index=False)
        pd.DataFrame(columns=["REGION", "STORAGE", "VALUE"]).to_csv(os.path.join(comparison_directory, "StorageMaxChargeRate.csv"), index=False)

