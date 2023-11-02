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
    CapacityToActivityUnit: RegionData | None

    # Capacity of one new unit of a technology
    # If specified the problem will turn into a Mixed Integer Linear Problem
    CapacityOfOneTechnologyUnit: RegionYearData | None

    # Capacity factor, lifespan, availability
    AvailabilityFactor: RegionYearData | None  # Maximum time a technology can run in the whole year, as a fraction from 0 to 1
    CapacityFactor: RegionYearTimeData | None
    OperationalLife: StringInt | None

    # financials
    CapitalCost: RegionYearData | None
    FixedCost: RegionYearData | None
    VariableCost: RegionModeYearData | None

    # initial capacity
    ResidualCapacity: RegionYearData | None

    # constraints - capacity
    TotalAnnualMaxCapacity: RegionYearData | None  # Maximum technology capacity (installed + residual) per year
    TotalAnnualMinCapacity: RegionYearData | None  # Minimum technology capacity (installed + residual) per year
    TotalAnnualMaxCapacityInvestment: RegionYearData | None  # Maximum technology capacity additions per year
    TotalAnnualMinCapacityInvestment: RegionYearData | None  # Minimum technology capacity additions per year

    # TODO
    # Relative growth rate restrictions not currently implemented in osemosys, can be added via change in osemosys code
    # additional_capacity_max_growth_rate: RegionYearData     # growth rate (<1.)
    # additional_capacity_max_ceil: RegionYearData            # Absolute value (ceil relative to growth rate)
    # additional_capacity_max_floor: RegionYearData           # absolute value (floor relative to growth rate)
    # additional_capacity_min_growth_rate: RegionYearData     # growth rate (<1.)

    # constraints - activity
    TotalTechnologyAnnualActivityUpperLimit: RegionYearData | None  # Maximum technology activity per year
    TotalTechnologyAnnualActivityLowerLimit: RegionYearData | None  # Minimum technology activity per year
    TotalTechnologyModelPeriodActivityUpperLimit: RegionData | None  # Maximum technology activity across whole modelled period
    TotalTechnologyModelPeriodActivityLowerLimit: RegionData | None  # Minimum technology activity across whole modelled period

    # activity ratios & efficiency
    EmissionActivityRatio: StringStringIntIntData | None  # Technology emission activity ratio by mode of operation
    InputActivityRatio: StringStringIntIntData | None  # Technology fuel input activity ratio by mode of operation
    OutputActivityRatio: StringStringIntIntData | None  # Technology fuel output activity ratio by mode of operation
    TechnologyToStorage: StringStringIntIntData | None  # Binary parameter linking a technology to the storage facility it charges (1 linked, 0 unlinked)
    TechnologyFromStorage: StringStringIntIntData | None  # Binary parameter linking a storage facility to the technology it feeds (1 linked, 0 unlinked)

    # Renewable technology tag
    RETagTechnology: RegionTechnologyYearData | None # Binary parameter indicating technologies that can contribute to renewable targets (1 RE, 0 non-RE)

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        df_technologies = pd.read_csv(os.path.join(root_dir, "TECHNOLOGY.csv"))

        parser_data = [
            {
                "name": "CapacityToActivityUnit",
                "filepath": "CapacityToActivityUnit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION"],
            },
            {
                "name": "CapacityOfOneTechnologyUnit",
                "filepath": "CapacityOfOneTechnologyUnit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "AvailabilityFactor",
                "filepath": "AvailabilityFactor.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "CapacityFactor",
                "filepath": "CapacityFactor.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "TIMESLICE", "YEAR"],
            },
            {
                "name": "OperationalLife",
                "filepath": "OperationalLife.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION"],
            },
            {
                "name": "CapitalCost",
                "filepath": "CapitalCost.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "FixedCost",
                "filepath": "FixedCost.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "VariableCost",
                "filepath": "VariableCost.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "MODE_OF_OPERATION", "YEAR"],
            },
            {
                "name": "ResidualCapacity",
                "filepath": "ResidualCapacity.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "TotalAnnualMaxCapacity",
                "filepath": "TotalAnnualMaxCapacity.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "TotalAnnualMinCapacity",
                "filepath": "TotalAnnualMinCapacity.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "TotalAnnualMaxCapacityInvestment",
                "filepath": "TotalAnnualMaxCapacityInvestment.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "TotalAnnualMinCapacityInvestment",
                "filepath": "TotalAnnualMinCapacityInvestment.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "TotalTechnologyAnnualActivityUpperLimit",
                "filepath": "TotalTechnologyAnnualActivityUpperLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "TotalTechnologyAnnualActivityLowerLimit",
                "filepath": "TotalTechnologyAnnualActivityLowerLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION"],
            },
            {
                "name": "TotalTechnologyModelPeriodActivityUpperLimit",
                "filepath": "TotalTechnologyModelPeriodActivityUpperLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION"],
            },
            {
                "name": "TotalTechnologyModelPeriodActivityLowerLimit",
                "filepath": "TotalTechnologyModelPeriodActivityLowerLimit.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "YEAR"],
            },
            {
                "name": "EmissionActivityRatio",
                "filepath": "EmissionActivityRatio.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "EMISSION", "MODE_OF_OPERATION", "YEAR"],
            },
            {
                "name": "InputActivityRatio",
                "filepath": "InputActivityRatio.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "FUEL", "MODE_OF_OPERATION", "YEAR"],
            },
            {
                "name": "OutputActivityRatio",
                "filepath": "OutputActivityRatio.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "FUEL", "MODE_OF_OPERATION", "YEAR"],
            },
            {
                "name": "TechnologyToStorage",
                "filepath": "TechnologyToStorage.csv",
                "root_column": "TECHNOLOGY",
                "data_columns": ["REGION", "STORAGE", "MODE_OF_OPERATION"],
            },
            {
                "name": "TechnologyFromStorage",
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
                    CapacityToActivityUnit=RegionData(
                        data=data_json_format["CapacityToActivityUnit"]
                    )
                    if data_json_format["CapacityToActivityUnit"] is not None
                    else None,
                    CapacityOfOneTechnologyUnit=RegionYearData(
                        data=data_json_format["CapacityOfOneTechnologyUnit"]
                    )
                    if data_json_format["CapacityOfOneTechnologyUnit"] is not None
                    else None,
                    AvailabilityFactor=RegionYearData(data=data_json_format["AvailabilityFactor"])
                    if data_json_format["AvailabilityFactor"] is not None
                    else None,
                    CapacityFactor=RegionYearTimeData(data=data_json_format["CapacityFactor"])
                    if data_json_format["CapacityFactor"] is not None
                    else None,
                    OperationalLife=StringInt(data=data_json_format["OperationalLife"])
                    if data_json_format["OperationalLife"] is not None
                    else None,
                    CapitalCost=RegionYearData(data=data_json_format["CapitalCost"])
                    if data_json_format["CapitalCost"] is not None
                    else None,
                    FixedCost=RegionYearData(data=data_json_format["FixedCost"])
                    if data_json_format["FixedCost"] is not None
                    else None,
                    VariableCost=RegionModeYearData(data=data_json_format["VariableCost"])
                    if data_json_format["VariableCost"] is not None
                    else None,
                    ResidualCapacity=RegionYearData(data=data_json_format["ResidualCapacity"])
                    if data_json_format["ResidualCapacity"] is not None
                    else None,
                    TotalAnnualMaxCapacity=RegionYearData(data=data_json_format["TotalAnnualMaxCapacity"])
                    if data_json_format["TotalAnnualMaxCapacity"] is not None
                    else None,
                    TotalAnnualMinCapacity=RegionYearData(data=data_json_format["TotalAnnualMinCapacity"])
                    if data_json_format["TotalAnnualMinCapacity"] is not None
                    else None,
                    TotalAnnualMaxCapacityInvestment=RegionYearData(
                        data=data_json_format["TotalAnnualMaxCapacityInvestment"]
                    )
                    if data_json_format["TotalAnnualMaxCapacityInvestment"] is not None
                    else None,
                    TotalAnnualMinCapacityInvestment=RegionYearData(
                        data=data_json_format["TotalAnnualMinCapacityInvestment"]
                    )
                    if data_json_format["TotalAnnualMinCapacityInvestment"] is not None
                    else None,
                    TotalTechnologyAnnualActivityUpperLimit=RegionYearData(data=data_json_format["TotalTechnologyAnnualActivityUpperLimit"])
                    if data_json_format["TotalTechnologyAnnualActivityUpperLimit"] is not None
                    else None,
                    TotalTechnologyAnnualActivityLowerLimit=RegionYearData(data=data_json_format["TotalTechnologyAnnualActivityLowerLimit"])
                    if data_json_format["TotalTechnologyAnnualActivityLowerLimit"] is not None
                    else None,
                    TotalTechnologyModelPeriodActivityUpperLimit=RegionData(data=data_json_format["TotalTechnologyModelPeriodActivityUpperLimit"])
                    if data_json_format["TotalTechnologyModelPeriodActivityUpperLimit"] is not None
                    else None,
                    TotalTechnologyModelPeriodActivityLowerLimit=RegionData(data=data_json_format["TotalTechnologyModelPeriodActivityLowerLimit"])
                    if data_json_format["TotalTechnologyModelPeriodActivityLowerLimit"] is not None
                    else None,
                    EmissionActivityRatio=StringStringIntIntData(
                        data=data_json_format["EmissionActivityRatio"]
                    )
                    if data_json_format["EmissionActivityRatio"] is not None
                    else None,
                    InputActivityRatio=StringStringIntIntData(
                        data=data_json_format["InputActivityRatio"]
                    )
                    if data_json_format["InputActivityRatio"] is not None
                    else None,
                    OutputActivityRatio=StringStringIntIntData(
                        data=data_json_format["OutputActivityRatio"]
                    )
                    if data_json_format["OutputActivityRatio"] is not None
                    else None,
                    TechnologyToStorage=StringStringIntIntData(data=data_json_format["TechnologyToStorage"])
                    if data_json_format["TechnologyToStorage"] is not None
                    else None,
                    TechnologyFromStorage=StringStringIntIntData(data=data_json_format["TechnologyFromStorage"])
                    if data_json_format["TechnologyFromStorage"] is not None
                    else None,
                    RETagTechnology=RegionTechnologyYearData(data=data_json_format["RETagTechnology"])
                    if data_json_format["RETagTechnology"] is not None
                    else None,
                )
            )

        return technology_instances
    

    def to_otoole_csv(self, comparison_directory) -> "cls":

        # CapacityToActivityUnit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.CapacityToActivityUnit, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="CapacityToActivityUnit.csv")
        # CapacityOfOneTechnologyUnit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.CapacityOfOneTechnologyUnit, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="CapacityOfOneTechnologyUnit.csv")
        # AvailabilityFactor
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.AvailabilityFactor, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="AvailabilityFactor.csv")
        # CapacityFactor
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.CapacityFactor, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "TIMESLICE", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="CapacityFactor.csv")
        # OperationalLife
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.OperationalLife, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="OperationalLife.csv")
        # CapitalCost
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.CapitalCost, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="CapitalCost.csv")
        # FixedCost
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.FixedCost, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="FixedCost.csv")
        # VariableCost
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.VariableCost, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="VariableCost.csv")
        # ResidualCapacity
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.ResidualCapacity, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="ResidualCapacity.csv")
        # TotalAnnualMaxCapacity
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TotalAnnualMaxCapacity, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalAnnualMaxCapacity.csv")
        # TotalAnnualMinCapacity
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TotalAnnualMinCapacity, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalAnnualMinCapacity.csv")
        # TotalAnnualMaxCapacityInvestment
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TotalAnnualMaxCapacityInvestment, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalAnnualMaxCapacityInvestment.csv")
        # TotalAnnualMinCapacityInvestment
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TotalAnnualMinCapacityInvestment, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalAnnualMinCapacityInvestment.csv")
        # TotalTechnologyAnnualActivityUpperLimit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TotalTechnologyAnnualActivityUpperLimit, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalTechnologyAnnualActivityUpperLimit.csv")
        # TotalTechnologyAnnualActivityLowerLimit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TotalTechnologyAnnualActivityLowerLimit, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalTechnologyAnnualActivityLowerLimit.csv")
        # TotalTechnologyModelPeriodActivityUpperLimit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TotalTechnologyModelPeriodActivityUpperLimit, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalTechnologyModelPeriodActivityUpperLimit.csv")
        # TotalTechnologyModelPeriodActivityLowerLimit
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TotalTechnologyModelPeriodActivityLowerLimit, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TotalTechnologyModelPeriodActivityLowerLimit.csv")
        # EmissionActivityRatio
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.EmissionActivityRatio, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "EMISSION", "MODE_OF_OPERATION", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="EmissionActivityRatio.csv")
        # InputActivityRatio
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.InputActivityRatio, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="InputActivityRatio.csv")
        # OutputActivityRatio
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.OutputActivityRatio, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="OutputActivityRatio.csv")
        # TechnologyToStorage
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TechnologyToStorage, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="TechnologyToStorage.csv")
        # TechnologyFromStorage
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.TechnologyFromStorage, 
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

    CapitalCostStorage: RegionYearData | None
    OperationalLifeStorage: RegionData | None
    MinStorageCharge: RegionYearData | None  # Lower bound to the amount of energy stored, as a fraction of the maximum, with a number reanging between 0 and 1
    StorageLevelStart: RegionData | None  # Level of storage at the beginning of first modelled year, in units of activity
    ResidualStorageCapacity: RegionYearData | None
    StorageMaxDischargeRate: RegionData | None  # Maximum discharging rate for the storage, in units of activity per year
    StorageMaxChargeRate: RegionData | None  # Maximum charging rate for the storage, in units of activity per year

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        df_storage_technologies = pd.read_csv(os.path.join(root_dir, "STORAGE.csv"))

        df_CapitalCostStorage = pd.read_csv(os.path.join(root_dir, "CapitalCostStorage.csv"))
        df_OperationalLifeStorage = pd.read_csv(os.path.join(root_dir, "OperationalLifeStorage.csv"))
        df_MinStorageCharge = pd.read_csv(os.path.join(root_dir, "MinStorageCharge.csv"))
        df_StorageLevelStart = pd.read_csv(os.path.join(root_dir, "StorageLevelStart.csv"))
        df_ResidualStorageCapacity = pd.read_csv(os.path.join(root_dir, "ResidualStorageCapacity.csv"))
        df_StorageMaxDischargeRate = pd.read_csv(os.path.join(root_dir, "StorageMaxDischargeRate.csv"))
        df_StorageMaxChargeRate = pd.read_csv(os.path.join(root_dir, "StorageMaxChargeRate.csv"))

        storage_instances = []
        for storage in df_storage_technologies["VALUE"].values.tolist():
            storage_instances.append(
                cls(
                    id=storage,
                    long_name=None,
                    description=None,
                    CapitalCostStorage=(
                        RegionYearData(
                            data=group_to_json(
                                g=df_CapitalCostStorage.loc[df_CapitalCostStorage["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_CapitalCostStorage["STORAGE"].values
                        else None
                    ),
                    OperationalLifeStorage=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_OperationalLifeStorage.loc[df_OperationalLifeStorage["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_OperationalLifeStorage["STORAGE"].values
                        else None
                    ),
                    MinStorageCharge=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_MinStorageCharge.loc[df_MinStorageCharge["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_MinStorageCharge["STORAGE"].values
                        else None
                    ),
                    StorageLevelStart=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_StorageLevelStart.loc[df_StorageLevelStart["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_StorageLevelStart["STORAGE"].values
                        else None
                    ),
                    ResidualStorageCapacity=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_ResidualStorageCapacity.loc[
                                    df_ResidualStorageCapacity["STORAGE"] == storage
                                ],
                                root_column="STORAGE",
                                data_columns=["REGION", "YEAR"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_ResidualStorageCapacity["STORAGE"].values
                        else None
                    ),
                    StorageMaxDischargeRate=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_StorageMaxDischargeRate.loc[
                                    df_StorageMaxDischargeRate["STORAGE"] == storage
                                ],
                                root_column="STORAGE",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_StorageMaxDischargeRate["STORAGE"].values
                        else None
                    ),
                    StorageMaxChargeRate=(
                        RegionTechnologyYearData(
                            data=group_to_json(
                                g=df_StorageMaxChargeRate.loc[df_StorageMaxChargeRate["STORAGE"] == storage],
                                root_column="STORAGE",
                                data_columns=["REGION"],
                                target_column="VALUE",
                            )
                        )
                        if storage in df_StorageMaxChargeRate["STORAGE"].values
                        else None
                    ),
                )
            )

        return storage_instances
    
    def to_otoole_csv(self, comparison_directory) -> "cls":

        # CapitalCostStorage
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.CapitalCostStorage, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "YEAR", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="CapitalCostStorage.csv")
        # OperationalLifeStorage
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.OperationalLifeStorage, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="OperationalLifeStorage.csv")
        # MinStorageCharge
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.MinStorageCharge, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "YEAR", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="MinStorageCharge.csv")
        # StorageLevelStart
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.StorageLevelStart, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="StorageLevelStart.csv")
        # ResidualStorageCapacity
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.ResidualStorageCapacity, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "YEAR", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="ResidualStorageCapacity.csv")
        # StorageMaxDischargeRate
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.StorageMaxDischargeRate, 
                         id=self.id, 
                         column_structure=["REGION", "STORAGE", "VALUE"], 
                         id_column="STORAGE", 
                         output_csv_name="StorageMaxDischargeRate.csv")
        # StorageMaxChargeRate
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.StorageMaxChargeRate, 
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

