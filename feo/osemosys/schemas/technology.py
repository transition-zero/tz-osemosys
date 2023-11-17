import os

import pandas as pd
from typing import ClassVar
from pathlib import Path
from pydantic import BaseModel, conlist, root_validator

from feo.osemosys.utils import *

from .base import *

# ##################
# ### TECHNOLOGY ###
# ##################

class OtooleCfg(BaseModel):
    """
    Paramters needed to round-trip csvs from otoole
    """

    empty_dfs: List[str] | None


class Technology(OSeMOSYSBase):
    """
    Class to contain all information pertaining to technologies (excluding storage technologies)
    """

    # Capacity unit to activity unit conversion
    # Conversion factor relating the energy that would be produced when one unit of capacity is fully used in one year.
    CapacityToActivityUnit: OSeMOSYSData | None

    # Capacity of one new unit of a technology
    # If specified the problem will turn into a Mixed Integer Linear Problem
    CapacityOfOneTechnologyUnit: OSeMOSYSData | None

    # Capacity factor, lifespan, availability
    AvailabilityFactor: OSeMOSYSData | None  # Maximum time a technology can run in the whole year, as a fraction from 0 to 1
    CapacityFactor: OSeMOSYSData | None
    OperationalLife: OSeMOSYSData | None

    # financials
    CapitalCost: OSeMOSYSData | None
    FixedCost: OSeMOSYSData | None
    VariableCost: OSeMOSYSData | None

    # initial capacity
    ResidualCapacity: OSeMOSYSData | None

    # constraints - capacity
    TotalAnnualMaxCapacity: OSeMOSYSData | None  # Maximum technology capacity (installed + residual) per year
    TotalAnnualMinCapacity: OSeMOSYSData | None  # Minimum technology capacity (installed + residual) per year
    TotalAnnualMaxCapacityInvestment: OSeMOSYSData | None  # Maximum technology capacity additions per year
    TotalAnnualMinCapacityInvestment: OSeMOSYSData | None  # Minimum technology capacity additions per year

    # TODO
    # Relative growth rate restrictions not currently implemented in osemosys, can be added via change in osemosys code
    # additional_capacity_max_growth_rate: RegionYearData     # growth rate (<1.)
    # additional_capacity_max_ceil: RegionYearData            # Absolute value (ceil relative to growth rate)
    # additional_capacity_max_floor: RegionYearData           # absolute value (floor relative to growth rate)
    # additional_capacity_min_growth_rate: RegionYearData     # growth rate (<1.)

    # constraints - activity
    TotalTechnologyAnnualActivityUpperLimit: OSeMOSYSData | None  # Maximum technology activity per year
    TotalTechnologyAnnualActivityLowerLimit: OSeMOSYSData | None  # Minimum technology activity per year
    TotalTechnologyModelPeriodActivityUpperLimit: OSeMOSYSData | None  # Maximum technology activity across whole modelled period
    TotalTechnologyModelPeriodActivityLowerLimit: OSeMOSYSData | None  # Minimum technology activity across whole modelled period

    # activity ratios & efficiency
    EmissionActivityRatio: OSeMOSYSData | None  # Technology emission activity ratio by mode of operation
    InputActivityRatio: OSeMOSYSData | None  # Technology fuel input activity ratio by mode of operation
    OutputActivityRatio: OSeMOSYSData | None  # Technology fuel output activity ratio by mode of operation
    TechnologyToStorage: OSeMOSYSData | None  # Binary parameter linking a technology to the storage facility it charges (1 linked, 0 unlinked)
    TechnologyFromStorage: OSeMOSYSData | None  # Binary parameter linking a storage facility to the technology it feeds (1 linked, 0 unlinked)

    # Renewable technology tag
    RETagTechnology: OSeMOSYSData | None # Binary parameter indicating technologies that can contribute to renewable targets (1 RE, 0 non-RE)

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[list[str]] = [
        "CapacityToActivityUnit",
        "CapacityOfOneTechnologyUnit",
        "AvailabilityFactor",
        "CapacityFactor",
        "OperationalLife",
        "CapitalCost",
        "FixedCost",
        "VariableCost",
        "ResidualCapacity",
        "TotalAnnualMaxCapacity",
        "TotalAnnualMinCapacity",
        "TotalAnnualMaxCapacityInvestment",
        "TotalAnnualMinCapacityInvestment",
        "TotalTechnologyAnnualActivityUpperLimit",
        "TotalTechnologyAnnualActivityLowerLimit",
        "TotalTechnologyModelPeriodActivityUpperLimit",
        "TotalTechnologyModelPeriodActivityLowerLimit",
        "EmissionActivityRatio",
        "InputActivityRatio",
        "OutputActivityRatio",
        "TechnologyToStorage",
        "TechnologyFromStorage",
        "RETagTechnology",
    ]

    @root_validator(pre=True)
    def construct_from_components(cls, values):
        CapacityToActivityUnit = values.get("CapacityToActivityUnit")
        CapacityOfOneTechnologyUnit = values.get("CapacityOfOneTechnologyUnit")
        AvailabilityFactor = values.get("AvailabilityFactor")
        CapacityFactor = values.get("CapacityFactor")
        OperationalLife = values.get("OperationalLife")
        CapitalCost = values.get("CapitalCost")
        FixedCost = values.get("FixedCost")
        VariableCost = values.get("VariableCost")
        ResidualCapacity = values.get("ResidualCapacity")
        TotalAnnualMaxCapacity = values.get("TotalAnnualMaxCapacity")
        TotalAnnualMinCapacity = values.get("TotalAnnualMinCapacity")
        TotalAnnualMaxCapacityInvestment = values.get("TotalAnnualMaxCapacityInvestment")
        TotalAnnualMinCapacityInvestment = values.get("TotalAnnualMinCapacityInvestment")
        TotalTechnologyAnnualActivityUpperLimit = values.get("TotalTechnologyAnnualActivityUpperLimit")
        TotalTechnologyAnnualActivityLowerLimit = values.get("TotalTechnologyAnnualActivityLowerLimit")
        TotalTechnologyModelPeriodActivityUpperLimit = values.get("TotalTechnologyModelPeriodActivityUpperLimit")
        TotalTechnologyModelPeriodActivityLowerLimit = values.get("TotalTechnologyModelPeriodActivityLowerLimit")
        EmissionActivityRatio = values.get("EmissionActivityRatio")
        InputActivityRatio = values.get("InputActivityRatio")
        OutputActivityRatio = values.get("OutputActivityRatio")
        TechnologyToStorage = values.get("TechnologyToStorage")
        TechnologyFromStorage = values.get("TechnologyFromStorage")
        RETagTechnology = values.get("RETagTechnology")

        return values
    

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        
        # ###########
        # Load Data #
        # ###########

        df_technologies = pd.read_csv(os.path.join(root_dir, "TECHNOLOGY.csv"))
        
        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key in cls.otoole_stems:
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)


        # ########################
        # Define class instances #
        # ########################

        technology_instances = []
        for technology in df_technologies["VALUE"].values.tolist():
            data_json_format = {}
            for stem in cls.otoole_stems:
                # If input CSV present
                if stem in dfs:
                    data_columns=dfs[stem].columns.tolist()
                    data_columns.remove("TECHNOLOGY")
                    data_columns.remove("VALUE")
                    data_json_format[stem] = (
                        group_to_json(
                            g=dfs[stem].loc[
                                dfs[stem]["TECHNOLOGY"] == technology
                            ],
                            root_column="TECHNOLOGY",
                            data_columns=data_columns,
                            target_column="VALUE",
                        )
                        if technology in dfs[stem]["TECHNOLOGY"].values
                        else None
                    )
                # If input CSV missing
                else:
                    data_json_format[stem] = None
            
            technology_instances.append(
                cls(
                    id=technology,
                    long_name=None,
                    description=None,
                    otoole_cfg=otoole_cfg,
                    CapacityToActivityUnit=OSeMOSYSData(
                        data=data_json_format["CapacityToActivityUnit"]
                    )
                    if data_json_format["CapacityToActivityUnit"] is not None
                    else None,
                    CapacityOfOneTechnologyUnit=OSeMOSYSData(
                        data=data_json_format["CapacityOfOneTechnologyUnit"]
                    )
                    if data_json_format["CapacityOfOneTechnologyUnit"] is not None
                    else None,
                    AvailabilityFactor=OSeMOSYSData(data=data_json_format["AvailabilityFactor"])
                    if data_json_format["AvailabilityFactor"] is not None
                    else None,
                    CapacityFactor=OSeMOSYSData(data=data_json_format["CapacityFactor"])
                    if data_json_format["CapacityFactor"] is not None
                    else None,
                    OperationalLife=OSeMOSYSData(data=data_json_format["OperationalLife"])
                    if data_json_format["OperationalLife"] is not None
                    else None,
                    CapitalCost=OSeMOSYSData(data=data_json_format["CapitalCost"])
                    if data_json_format["CapitalCost"] is not None
                    else None,
                    FixedCost=OSeMOSYSData(data=data_json_format["FixedCost"])
                    if data_json_format["FixedCost"] is not None
                    else None,
                    VariableCost=OSeMOSYSData(data=data_json_format["VariableCost"])
                    if data_json_format["VariableCost"] is not None
                    else None,
                    ResidualCapacity=OSeMOSYSData(data=data_json_format["ResidualCapacity"])
                    if data_json_format["ResidualCapacity"] is not None
                    else None,
                    TotalAnnualMaxCapacity=OSeMOSYSData(data=data_json_format["TotalAnnualMaxCapacity"])
                    if data_json_format["TotalAnnualMaxCapacity"] is not None
                    else None,
                    TotalAnnualMinCapacity=OSeMOSYSData(data=data_json_format["TotalAnnualMinCapacity"])
                    if data_json_format["TotalAnnualMinCapacity"] is not None
                    else None,
                    TotalAnnualMaxCapacityInvestment=OSeMOSYSData(
                        data=data_json_format["TotalAnnualMaxCapacityInvestment"]
                    )
                    if data_json_format["TotalAnnualMaxCapacityInvestment"] is not None
                    else None,
                    TotalAnnualMinCapacityInvestment=OSeMOSYSData(
                        data=data_json_format["TotalAnnualMinCapacityInvestment"]
                    )
                    if data_json_format["TotalAnnualMinCapacityInvestment"] is not None
                    else None,
                    TotalTechnologyAnnualActivityUpperLimit=OSeMOSYSData(data=data_json_format["TotalTechnologyAnnualActivityUpperLimit"])
                    if data_json_format["TotalTechnologyAnnualActivityUpperLimit"] is not None
                    else None,
                    TotalTechnologyAnnualActivityLowerLimit=OSeMOSYSData(data=data_json_format["TotalTechnologyAnnualActivityLowerLimit"])
                    if data_json_format["TotalTechnologyAnnualActivityLowerLimit"] is not None
                    else None,
                    TotalTechnologyModelPeriodActivityUpperLimit=OSeMOSYSData(data=data_json_format["TotalTechnologyModelPeriodActivityUpperLimit"])
                    if data_json_format["TotalTechnologyModelPeriodActivityUpperLimit"] is not None
                    else None,
                    TotalTechnologyModelPeriodActivityLowerLimit=OSeMOSYSData(data=data_json_format["TotalTechnologyModelPeriodActivityLowerLimit"])
                    if data_json_format["TotalTechnologyModelPeriodActivityLowerLimit"] is not None
                    else None,
                    EmissionActivityRatio=OSeMOSYSData(
                        data=data_json_format["EmissionActivityRatio"]
                    )
                    if data_json_format["EmissionActivityRatio"] is not None
                    else None,
                    InputActivityRatio=OSeMOSYSData(
                        data=data_json_format["InputActivityRatio"]
                    )
                    if data_json_format["InputActivityRatio"] is not None
                    else None,
                    OutputActivityRatio=OSeMOSYSData(
                        data=data_json_format["OutputActivityRatio"]
                    )
                    if data_json_format["OutputActivityRatio"] is not None
                    else None,
                    TechnologyToStorage=OSeMOSYSData(data=data_json_format["TechnologyToStorage"])
                    if data_json_format["TechnologyToStorage"] is not None
                    else None,
                    TechnologyFromStorage=OSeMOSYSData(data=data_json_format["TechnologyFromStorage"])
                    if data_json_format["TechnologyFromStorage"] is not None
                    else None,
                    RETagTechnology=OSeMOSYSData(data=data_json_format["RETagTechnology"])
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

