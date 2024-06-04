import os
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Dict, List, Union

import pandas as pd
from pydantic import BaseModel, Field

from tz.osemosys.defaults import defaults
from tz.osemosys.logger import logging
from tz.osemosys.schemas.base import OSeMOSYSData
from tz.osemosys.schemas.compat.base import OtooleCfg
from tz.osemosys.utils import flatten, group_to_json

if TYPE_CHECKING:
    from tz.osemosys.schemas.technology import Technology


class OtooleTechnology(BaseModel):
    """
    Class to contain methods for converting Technology data to and from otoole style CSVs
    """

    otoole_cfg: OtooleCfg | None = Field(None)
    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "CapacityAdditionalMaxGrowthRate": {
            "attribute": "capacity_additional_max_growth_rate",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "CapacityAdditionalMinGrowthRate": {
            "attribute": "capacity_additional_min_growth_rate",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "CapacityAdditionalMaxFloor": {
            "attribute": "capacity_additional_max_floor",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "CapacityToActivityUnit": {
            "attribute": "capacity_activity_unit_ratio",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "CapacityOfOneTechnologyUnit": {
            "attribute": "capacity_one_tech_unit",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "AvailabilityFactor": {
            "attribute": "availability_factor",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "CapacityFactor": {
            "attribute": "capacity_factor",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "TIMESLICE", "VALUE"],
        },
        "OperationalLife": {
            "attribute": "operating_life",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "CapitalCost": {
            "attribute": "capex",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "FixedCost": {
            "attribute": "opex_fixed",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "VariableCost": {
            "attribute": "opex_variable",
            "columns": ["MODE_OF_OPERATION", "REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "ResidualCapacity": {
            "attribute": "residual_capacity",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "TotalAnnualMaxCapacity": {
            "attribute": "capacity_gross_max",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "TotalAnnualMinCapacity": {
            "attribute": "capacity_gross_min",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "TotalAnnualMaxCapacityInvestment": {
            "attribute": "capacity_additional_max",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "TotalAnnualMinCapacityInvestment": {
            "attribute": "capacity_additional_min",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "TotalTechnologyAnnualActivityUpperLimit": {
            "attribute": "activity_annual_max",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "TotalTechnologyAnnualActivityLowerLimit": {
            "attribute": "activity_annual_min",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "TotalTechnologyModelPeriodActivityUpperLimit": {
            "attribute": "activity_total_max",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "TotalTechnologyModelPeriodActivityLowerLimit": {
            "attribute": "activity_total_min",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "EmissionActivityRatio": {
            "attribute": "emission_activity_ratio",
            "columns": [
                "MODE_OF_OPERATION",
                "REGION",
                "TECHNOLOGY",
                "EMISSION",
                "YEAR",
                "VALUE",
            ],
        },
        "InputActivityRatio": {
            "attribute": "input_activity_ratio",
            "columns": [
                "MODE_OF_OPERATION",
                "REGION",
                "TECHNOLOGY",
                "FUEL",
                "YEAR",
                "VALUE",
            ],
        },
        "OutputActivityRatio": {
            "attribute": "output_activity_ratio",
            "columns": [
                "MODE_OF_OPERATION",
                "REGION",
                "TECHNOLOGY",
                "FUEL",
                "YEAR",
                "VALUE",
            ],
        },
        "TechnologyToStorage": {
            "attribute": "to_storage",
            "columns": [
                "MODE_OF_OPERATION",
                "REGION",
                "TECHNOLOGY",
                "STORAGE",
                "VALUE",
            ],
        },
        "TechnologyFromStorage": {
            "attribute": "from_storage",
            "columns": [
                "MODE_OF_OPERATION",
                "REGION",
                "TECHNOLOGY",
                "STORAGE",
                "VALUE",
            ],
        },
        "RETagTechnology": {
            "attribute": "include_in_joint_renewable_target",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
    }
    operating_mode_stem_translation: ClassVar[dict[str, str]] = {
        "VariableCost": ("opex_variable", OSeMOSYSData.RY),
        "EmissionActivityRatio": ("emission_activity_ratio", OSeMOSYSData.RIY),
        "InputActivityRatio": ("input_activity_ratio", OSeMOSYSData.RCY),
        "OutputActivityRatio": ("output_activity_ratio", OSeMOSYSData.RCY),
        "TechnologyToStorage": ("to_storage", OSeMOSYSData.RO.Bool),
        "TechnologyFromStorage": ("from_storage", OSeMOSYSData.RO.Bool),
    }

    @classmethod
    def from_otoole_csv(cls, root_dir) -> List["Technology"]:
        #############
        # Load Data #
        #############

        df_technologies = pd.read_csv(os.path.join(root_dir, "TECHNOLOGY.csv"))

        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[], non_default_idx={})
        for key, params in list(cls.otoole_stems.items()):
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
                else:
                    otoole_cfg.non_default_idx[key] = (
                        dfs[key].set_index([c for c in params["columns"] if c != "VALUE"]).index
                    )
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)

        #####################
        # Basic Data Checks #
        #####################

        # Check no duplicates in TECHNOLOGY.csv
        if len(df_technologies) != len(df_technologies["VALUE"].unique()):
            raise ValueError("TECHNOLOGY.csv must not contain duplicate values")

        # Check technology names are consistent with those in TECHNOLOGY.csv
        for df in dfs.keys():
            for technology in dfs[df]["TECHNOLOGY"].unique():
                if technology not in list(df_technologies["VALUE"]):
                    raise ValueError(f"{technology} given in {df}.csv but not in TECHNOLOGY.csv")

        ##########################
        # Define class instances #
        ##########################

        technology_instances = []
        for technology in df_technologies["VALUE"].values.tolist():
            data_json_format = {}
            for stem, params in cls.otoole_stems.items():
                # If input CSV present
                if stem in dfs:
                    data_columns = [
                        c for c in params["columns"] if c not in ["TECHNOLOGY", "VALUE"]
                    ]
                    data_json_format[stem] = (
                        group_to_json(
                            g=dfs[stem].loc[dfs[stem]["TECHNOLOGY"] == technology],
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

            operating_mode_ids = set(
                flatten(
                    [
                        list(data_json_format[stem].keys())
                        for stem in cls.operating_mode_stem_translation.keys()
                        if data_json_format[stem] is not None
                    ]
                )
            )

            operating_modes = []
            for op_mode_id in operating_mode_ids:
                op_mode_data = {}
                for stem, (
                    attribute,
                    osemosys_datatype,
                ) in cls.operating_mode_stem_translation.items():
                    if data_json_format[stem] is not None:
                        if op_mode_id in data_json_format[stem]:
                            op_mode_data[attribute] = osemosys_datatype(
                                data=data_json_format[stem][op_mode_id]
                            )
                op_mode_data["id"] = op_mode_id
                operating_modes.append(op_mode_data)

            technology_instances.append(
                cls(
                    id=technology,
                    otoole_cfg=otoole_cfg,
                    operating_modes=operating_modes,
                    capacity_activity_unit_ratio=(
                        OSeMOSYSData.R(data=data_json_format["CapacityToActivityUnit"])
                        if data_json_format["CapacityToActivityUnit"] is not None
                        else OSeMOSYSData.R(defaults.technology_capacity_activity_unit_ratio)
                    ),
                    capacity_one_tech_unit=(
                        OSeMOSYSData.RY(data=data_json_format["CapacityOfOneTechnologyUnit"])
                        if data_json_format["CapacityOfOneTechnologyUnit"] is not None
                        else None
                    ),
                    availability_factor=(
                        OSeMOSYSData.RY(data=data_json_format["AvailabilityFactor"])
                        if data_json_format["AvailabilityFactor"] is not None
                        else OSeMOSYSData.RY(defaults.technology_availability_factor)
                    ),
                    capacity_factor=(
                        OSeMOSYSData.RYS(data=data_json_format["CapacityFactor"])
                        if data_json_format["CapacityFactor"] is not None
                        else OSeMOSYSData.RYS(defaults.technology_capacity_factor)
                    ),
                    operating_life=(
                        OSeMOSYSData.R.Int(data=data_json_format["OperationalLife"])
                        if data_json_format["OperationalLife"] is not None
                        else OSeMOSYSData.R.Int(defaults.technology_operating_life)
                    ),
                    capex=(
                        OSeMOSYSData.RY(data=data_json_format["CapitalCost"])
                        if data_json_format["CapitalCost"] is not None
                        else OSeMOSYSData.RY(defaults.technology_capex)
                    ),
                    opex_fixed=(
                        OSeMOSYSData.RY(data=data_json_format["FixedCost"])
                        if data_json_format["FixedCost"] is not None
                        else OSeMOSYSData.RY(defaults.technology_opex_fixed_cost)
                    ),
                    residual_capacity=(
                        OSeMOSYSData.RY(data=data_json_format["ResidualCapacity"])
                        if data_json_format["ResidualCapacity"] is not None
                        else OSeMOSYSData.RY(defaults.technology_residual_capacity)
                    ),
                    capacity_gross_max=(
                        OSeMOSYSData.RY(data=data_json_format["TotalAnnualMaxCapacity"])
                        if data_json_format["TotalAnnualMaxCapacity"] is not None
                        else None
                    ),
                    capacity_gross_min=(
                        OSeMOSYSData.RY(data=data_json_format["TotalAnnualMinCapacity"])
                        if data_json_format["TotalAnnualMinCapacity"] is not None
                        else None
                    ),
                    capacity_additional_max=(
                        OSeMOSYSData.RY(data=data_json_format["TotalAnnualMaxCapacityInvestment"])
                        if data_json_format["TotalAnnualMaxCapacityInvestment"] is not None
                        else None
                    ),
                    capacity_additional_min=(
                        OSeMOSYSData.RY(data=data_json_format["TotalAnnualMinCapacityInvestment"])
                        if data_json_format["TotalAnnualMinCapacityInvestment"] is not None
                        else None
                    ),
                    activity_annual_max=(
                        OSeMOSYSData.RY(
                            data=data_json_format["TotalTechnologyAnnualActivityUpperLimit"]
                        )
                        if data_json_format["TotalTechnologyAnnualActivityUpperLimit"] is not None
                        else None
                    ),
                    activity_annual_min=(
                        OSeMOSYSData.RY(
                            data=data_json_format["TotalTechnologyAnnualActivityLowerLimit"]
                        )
                        if data_json_format["TotalTechnologyAnnualActivityLowerLimit"] is not None
                        else None
                    ),
                    activity_total_max=(
                        OSeMOSYSData.R(
                            data=data_json_format["TotalTechnologyModelPeriodActivityUpperLimit"]
                        )
                        if data_json_format["TotalTechnologyModelPeriodActivityUpperLimit"]
                        is not None
                        else None
                    ),
                    activity_total_min=(
                        OSeMOSYSData.R(
                            data=data_json_format["TotalTechnologyModelPeriodActivityLowerLimit"]
                        )
                        if data_json_format["TotalTechnologyModelPeriodActivityLowerLimit"]
                        is not None
                        else None
                    ),
                    include_in_joint_renewable_target=(
                        OSeMOSYSData.RY.Bool(data=data_json_format["RETagTechnology"])
                        if data_json_format["RETagTechnology"] is not None
                        else None
                    ),
                )
            )

        return technology_instances

    @classmethod
    def to_dataframes(cls, technologies: List["Technology"]) -> Dict[str, pd.DataFrame]:
        """Write a number of Technology objects to otoole-organised csvs.

        Args:
            technologies (List[Technology]): A list of Technology instances
            output_directory (str): Path to the root of the otoole csv directory
        """

        # TODO: it's getting wet. Refactor into functions alongside other compat methods

        # collect dataframes
        dfs = {}

        # add sets
        dfs["TECHNOLOGY"] = pd.DataFrame({"VALUE": [technology.id for technology in technologies]})
        dfs["MODE_OF_OPERATION"] = pd.DataFrame(
            {
                "VALUE": list(
                    {mode.id for technology in technologies for mode in technology.operating_modes}
                )
            }
        )

        # Parameters
        for technology in technologies:
            omitted_fields = []
            for stem, params in cls.otoole_stems.items():
                if stem not in cls.operating_mode_stem_translation.keys():
                    if getattr(technology, params["attribute"]) is not None:
                        if getattr(technology, params["attribute"]).is_composed:
                            columns = [
                                c for c in params["columns"] if c not in ["TECHNOLOGY", "VALUE"]
                            ]
                            df = pd.json_normalize(
                                getattr(technology, params["attribute"]).data
                            ).T.rename(columns={0: "VALUE"})
                            df["TECHNOLOGY"] = technology.id
                            df[columns] = pd.DataFrame(
                                df.index.str.split(".").to_list(), index=df.index
                            )
                            if stem in dfs:
                                dfs[stem].append(df)
                            else:
                                dfs[stem] = [df]
                        else:
                            # do something else or nothing with non-composed data
                            omitted_fields.append(stem)

            for stem, (
                attribute,
                _osemosys_datatype,
            ) in cls.operating_mode_stem_translation.items():
                for mode in technology.operating_modes:
                    if getattr(mode, attribute) is not None:
                        if getattr(mode, attribute).is_composed:
                            df = pd.json_normalize(getattr(mode, attribute).data).T.rename(
                                columns={0: "VALUE"}
                            )
                            df["TECHNOLOGY"] = technology.id
                            df["MODE_OF_OPERATION"] = mode.id
                            columns = [
                                c
                                for c in cls.otoole_stems[stem]["columns"]
                                if c not in ["TECHNOLOGY", "VALUE", "MODE_OF_OPERATION"]
                            ]
                            df[columns] = pd.DataFrame(
                                df.index.str.split(".").to_list(), index=df.index
                            )
                            if stem in dfs:
                                dfs[stem].append(df)
                            else:
                                dfs[stem] = [df]
                        else:
                            omitted_fields.append(stem)

            if omitted_fields:
                logging.warning(
                    f"{technology.id}: Data for {omitted_fields} not composed - omitting."
                )

        for stem in cls.operating_mode_stem_translation.keys():
            if stem in dfs:
                dfs[stem] = pd.concat(dfs[stem])

        for stem in cls.otoole_stems.keys():
            if stem not in cls.operating_mode_stem_translation.keys():
                if stem in dfs:
                    dfs[stem] = pd.concat(dfs[stem])

        return dfs

    @classmethod
    def to_otoole_csv(cls, technologies: List["Technology"], output_directory: Union[str, Path]):
        dfs = cls.to_dataframes(technologies)

        # Sets
        dfs["TECHNOLOGY"].to_csv(os.path.join(output_directory, "TECHNOLOGY.csv"), index=False)
        dfs["MODE_OF_OPERATION"].to_csv(
            os.path.join(output_directory, "MODE_OF_OPERATION.csv"), index=False
        )

        # write dataframes
        for stem, params in cls.otoole_stems.items():
            if (
                any([(stem not in technology.otoole_cfg.empty_dfs) for technology in technologies])
                and stem in dfs
            ):
                # cast OPERATING_MODE and YEAR back to int
                for col in ["YEAR", "MODE_OF_OPERATION"]:
                    if col in dfs[stem].columns:
                        dfs[stem][col] = dfs[stem][col].astype(int)
                (
                    dfs[stem]
                    .set_index([c for c in params["columns"] if c != "VALUE"])
                    .loc[technologies[0].otoole_cfg.non_default_idx[stem]]
                    .reset_index()
                    .to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)
                )

        return True
