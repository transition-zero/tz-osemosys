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
    capacity_activity_unit_ratio: OSeMOSYSData | None

    # Capacity of one new unit of a technology
    # If specified the problem will turn into a Mixed Integer Linear Problem
    capacity_one_tech_unit: OSeMOSYSData | None

    # Capacity factor, lifespan, availability
    availability_factor: OSeMOSYSData | None  # Maximum time a technology can run in the whole year, as a fraction from 0 to 1
    capacity_factor: OSeMOSYSData | None
    operating_life: OSeMOSYSData | None

    # financials
    capex: OSeMOSYSData | None
    opex_fixed: OSeMOSYSData | None
    opex_variable: OSeMOSYSData | None

    # initial capacity
    residual_capacity: OSeMOSYSData | None

    # constraints - capacity
    capacity_gross_max: OSeMOSYSData | None  # Maximum technology capacity (installed + residual) per year
    capacity_gross_min: OSeMOSYSData | None  # Minimum technology capacity (installed + residual) per year
    capacity_additional_max: OSeMOSYSData | None  # Maximum technology capacity additions per year
    capacity_additional_min: OSeMOSYSData | None  # Minimum technology capacity additions per year

    # TODO
    # Relative growth rate restrictions not currently implemented in osemosys, can be added via change in osemosys code
    # additional_capacity_max_growth_rate: RegionYearData     # growth rate (<1.)
    # additional_capacity_max_ceil: RegionYearData            # Absolute value (ceil relative to growth rate)
    # additional_capacity_max_floor: RegionYearData           # absolute value (floor relative to growth rate)
    # additional_capacity_min_growth_rate: RegionYearData     # growth rate (<1.)

    # constraints - activity
    activity_annual_max: OSeMOSYSData | None  # Maximum technology activity per year
    activity_annual_min: OSeMOSYSData | None  # Minimum technology activity per year
    activity_total_max: OSeMOSYSData | None  # Maximum technology activity across whole modelled period
    activity_total_min: OSeMOSYSData | None  # Minimum technology activity across whole modelled period

    # activity ratios & efficiency
    emission_activity_ratio: OSeMOSYSData | None  # Technology emission activity ratio by mode of operation
    input_activity_ratio: OSeMOSYSData | None  # Technology fuel input activity ratio by mode of operation
    output_activity_ratio: OSeMOSYSData | None  # Technology fuel output activity ratio by mode of operation
    to_storage: OSeMOSYSData | None  # Binary parameter linking a technology to the storage facility it charges (1 linked, 0 unlinked)
    from_storage: OSeMOSYSData | None  # Binary parameter linking a storage facility to the technology it feeds (1 linked, 0 unlinked)

    # Renewable technology tag
    is_renewable: OSeMOSYSData | None # Binary parameter indicating technologies that can contribute to renewable targets (1 RE, 0 non-RE)

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
        capacity_activity_unit_ratio = values.get("capacity_activity_unit_ratio")
        capacity_one_tech_unit = values.get("capacity_one_tech_unit")
        availability_factor = values.get("availability_factor")
        capacity_factor = values.get("capacity_factor")
        operating_life = values.get("operating_life")
        capex = values.get("capex")
        opex_fixed = values.get("opex_fixed")
        opex_variable = values.get("opex_variable")
        residual_capacity = values.get("residual_capacity")
        capacity_gross_max = values.get("capacity_gross_max")
        capacity_gross_min = values.get("capacity_gross_min")
        capacity_additional_max = values.get("capacity_additional_max")
        capacity_additional_min = values.get("capacity_additional_min")
        activity_annual_max = values.get("activity_annual_max")
        activity_annual_min = values.get("activity_annual_min")
        activity_total_max = values.get("activity_total_max")
        activity_total_min = values.get("activity_total_min")
        emission_activity_ratio = values.get("emission_activity_ratio")
        input_activity_ratio = values.get("input_activity_ratio")
        output_activity_ratio = values.get("output_activity_ratio")
        to_storage = values.get("to_storage")
        from_storage = values.get("from_storage")
        is_renewable = values.get("is_renewable")

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
                    capacity_activity_unit_ratio=OSeMOSYSData(
                        data=data_json_format["CapacityToActivityUnit"]
                    )
                    if data_json_format["CapacityToActivityUnit"] is not None
                    else None,
                    capacity_one_tech_unit=OSeMOSYSData(
                        data=data_json_format["CapacityOfOneTechnologyUnit"]
                    )
                    if data_json_format["CapacityOfOneTechnologyUnit"] is not None
                    else None,
                    availability_factor=OSeMOSYSData(data=data_json_format["AvailabilityFactor"])
                    if data_json_format["AvailabilityFactor"] is not None
                    else None,
                    capacity_factor=OSeMOSYSData(data=data_json_format["CapacityFactor"])
                    if data_json_format["CapacityFactor"] is not None
                    else None,
                    operating_life=OSeMOSYSData(data=data_json_format["OperationalLife"])
                    if data_json_format["OperationalLife"] is not None
                    else None,
                    capex=OSeMOSYSData(data=data_json_format["CapitalCost"])
                    if data_json_format["CapitalCost"] is not None
                    else None,
                    opex_fixed=OSeMOSYSData(data=data_json_format["FixedCost"])
                    if data_json_format["FixedCost"] is not None
                    else None,
                    opex_variable=OSeMOSYSData(data=data_json_format["VariableCost"])
                    if data_json_format["VariableCost"] is not None
                    else None,
                    residual_capacity=OSeMOSYSData(data=data_json_format["ResidualCapacity"])
                    if data_json_format["ResidualCapacity"] is not None
                    else None,
                    capacity_gross_max=OSeMOSYSData(data=data_json_format["TotalAnnualMaxCapacity"])
                    if data_json_format["TotalAnnualMaxCapacity"] is not None
                    else None,
                    capacity_gross_min=OSeMOSYSData(data=data_json_format["TotalAnnualMinCapacity"])
                    if data_json_format["TotalAnnualMinCapacity"] is not None
                    else None,
                    capacity_additional_max=OSeMOSYSData(
                        data=data_json_format["TotalAnnualMaxCapacityInvestment"]
                    )
                    if data_json_format["TotalAnnualMaxCapacityInvestment"] is not None
                    else None,
                    capacity_additional_min=OSeMOSYSData(
                        data=data_json_format["TotalAnnualMinCapacityInvestment"]
                    )
                    if data_json_format["TotalAnnualMinCapacityInvestment"] is not None
                    else None,
                    activity_annual_max=OSeMOSYSData(data=data_json_format["TotalTechnologyAnnualActivityUpperLimit"])
                    if data_json_format["TotalTechnologyAnnualActivityUpperLimit"] is not None
                    else None,
                    activity_annual_min=OSeMOSYSData(data=data_json_format["TotalTechnologyAnnualActivityLowerLimit"])
                    if data_json_format["TotalTechnologyAnnualActivityLowerLimit"] is not None
                    else None,
                    activity_total_max=OSeMOSYSData(data=data_json_format["TotalTechnologyModelPeriodActivityUpperLimit"])
                    if data_json_format["TotalTechnologyModelPeriodActivityUpperLimit"] is not None
                    else None,
                    activity_total_min=OSeMOSYSData(data=data_json_format["TotalTechnologyModelPeriodActivityLowerLimit"])
                    if data_json_format["TotalTechnologyModelPeriodActivityLowerLimit"] is not None
                    else None,
                    emission_activity_ratio=OSeMOSYSData(
                        data=data_json_format["EmissionActivityRatio"]
                    )
                    if data_json_format["EmissionActivityRatio"] is not None
                    else None,
                    input_activity_ratio=OSeMOSYSData(
                        data=data_json_format["InputActivityRatio"]
                    )
                    if data_json_format["InputActivityRatio"] is not None
                    else None,
                    output_activity_ratio=OSeMOSYSData(
                        data=data_json_format["OutputActivityRatio"]
                    )
                    if data_json_format["OutputActivityRatio"] is not None
                    else None,
                    to_storage=OSeMOSYSData(data=data_json_format["TechnologyToStorage"])
                    if data_json_format["TechnologyToStorage"] is not None
                    else None,
                    from_storage=OSeMOSYSData(data=data_json_format["TechnologyFromStorage"])
                    if data_json_format["TechnologyFromStorage"] is not None
                    else None,
                    is_renewable=OSeMOSYSData(data=data_json_format["RETagTechnology"])
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
        # is_renewable
        to_csv_iterative(comparison_directory=comparison_directory, 
                         data=self.is_renewable, 
                         id=self.id, 
                         column_structure=["REGION", "TECHNOLOGY", "YEAR", "VALUE"], 
                         id_column="TECHNOLOGY", 
                         output_csv_name="RETagTechnology.csv")
        
        
        
        

class TechnologyStorage(OSeMOSYSBase):
    """
    Class to contain all information pertaining to storage technologies
    """

    capex: OSeMOSYSData | None
    operating_life: OSeMOSYSData | None
    minimum_charge: OSeMOSYSData | None  # Lower bound to the amount of energy stored, as a fraction of the maximum, with a number reanging between 0 and 1
    initial_level: OSeMOSYSData | None  # Level of storage at the beginning of first modelled year, in units of activity
    residual_capacity: OSeMOSYSData | None
    max_discharge_rate: OSeMOSYSData | None  # Maximum discharging rate for the storage, in units of activity per year
    max_charge_rate: OSeMOSYSData | None  # Maximum charging rate for the storage, in units of activity per year

    otoole_cfg: OtooleCfg | None
    otoole_stems: ClassVar[list[str]] = [
        "CapitalCostStorage",
        "OperationalLifeStorage",
        "MinStorageCharge",
        "StorageLevelStart",
        "ResidualStorageCapacity",
        "StorageMaxDischargeRate",
        "StorageMaxChargeRate",
    ]

    @root_validator(pre=True)
    def construct_from_components(cls, values):
        capex = values.get("capex")
        operating_life = values.get("operating_life")
        minimum_charge = values.get("minimum_charge")
        initial_level = values.get("initial_level")
        residual_capacity = values.get("residual_capacity")
        max_discharge_rate = values.get("max_discharge_rate")
        max_charge_rate = values.get("max_charge_rate")
        
        return values

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["cls"]:
        
        # ###########
        # Load Data #
        # ###########

        df_storage_technologies = pd.read_csv(os.path.join(root_dir, "STORAGE.csv"))

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
        
        storage_instances = []
        for storage in df_storage_technologies["VALUE"].values.tolist():
            data_json_format = {}
            for stem in cls.otoole_stems:
                # If input CSV present
                if stem in dfs:
                    data_columns=dfs[stem].columns.tolist()
                    data_columns.remove("STORAGE")
                    data_columns.remove("VALUE")
                    data_json_format[stem] = (
                        group_to_json(
                            g=dfs[stem].loc[
                                dfs[stem]["STORAGE"] == storage
                            ],
                            root_column="STORAGE",
                            data_columns=data_columns,
                            target_column="VALUE",
                        )
                        if storage in dfs[stem]["STORAGE"].values
                        else None
                    )
                # If input CSV missing
                else:
                    data_json_format[stem] = None
        
            storage_instances.append(
                cls(
                    id=storage,
                    long_name=None,
                    description=None,
                    otoole_cfg=otoole_cfg,
                    capex=OSeMOSYSData(
                        data=data_json_format["CapitalCostStorage"]
                    )
                    if data_json_format["CapitalCostStorage"] is not None
                    else None,
                    operating_life=OSeMOSYSData(
                        data=data_json_format["OperationalLifeStorage"]
                    )
                    if data_json_format["OperationalLifeStorage"] is not None
                    else None,
                    minimum_charge=OSeMOSYSData(data=data_json_format["MinStorageCharge"])
                    if data_json_format["MinStorageCharge"] is not None
                    else None,
                    initial_level=OSeMOSYSData(data=data_json_format["StorageLevelStart"])
                    if data_json_format["StorageLevelStart"] is not None
                    else None,
                    residual_capacity=OSeMOSYSData(data=data_json_format["ResidualStorageCapacity"])
                    if data_json_format["ResidualStorageCapacity"] is not None
                    else None,
                    max_discharge_rate=OSeMOSYSData(data=data_json_format["StorageMaxDischargeRate"])
                    if data_json_format["StorageMaxDischargeRate"] is not None
                    else None,
                    max_charge_rate=OSeMOSYSData(data=data_json_format["StorageMaxChargeRate"])
                    if data_json_format["StorageMaxChargeRate"] is not None
                    else None,
                    
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

