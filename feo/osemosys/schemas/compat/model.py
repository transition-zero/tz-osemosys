import os
from pathlib import Path
from typing import ClassVar, Union

import pandas as pd
import xarray as xr
from pydantic import BaseModel, Field

from feo.osemosys.defaults import defaults
from feo.osemosys.schemas.base import OSeMOSYSData
from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.schemas.compat.base import DefaultsOtoole, OtooleCfg
from feo.osemosys.schemas.impact import Impact
from feo.osemosys.schemas.region import Region
from feo.osemosys.schemas.technology import Technology, TechnologyStorage
from feo.osemosys.schemas.time_definition import TimeDefinition
from feo.osemosys.utils import group_to_json, merge, to_df_helper


class RunSpecOtoole(BaseModel):
    otoole_cfg: OtooleCfg | None = Field(None)

    # Default values
    defaults_otoole: DefaultsOtoole | None = Field(None)

    otoole_stems: ClassVar[dict[str : dict[str : Union[str, list[str]]]]] = {
        "ReserveMargin": {
            "attribute": "reserve_margin",
            "columns": ["REGION", "YEAR", "VALUE"],
        },
        "ReserveMarginTagFuel": {
            "attribute": "reserve_margin",
            "columns": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
        "ReserveMarginTagTechnology": {
            "attribute": "reserve_margin",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "REMinProductionTarget": {
            "attribute": "renewable_production_target",
            "columns": ["REGION", "YEAR", "VALUE"],
        },
        "RETagFuel": {
            "attribute": "renewable_production_target",
            "columns": ["REGION", "FUEL", "YEAR", "VALUE"],
        },
        "RETagTechnology": {
            "attribute": "renewable_production_target",
            "columns": ["REGION", "TECHNOLOGY", "YEAR", "VALUE"],
        },
        "DepreciationMethod": {
            "attribute": "depreciation_method",
            "columns": ["REGION", "VALUE"],
        },
        "DiscountRate": {
            "attribute": "discount_rate",
            "columns": ["REGION", "VALUE"],
        },
        "DiscountRateIdv": {
            "attribute": "discount_rate",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
    }

    def to_xr_ds(self):
        """
        Return the current RunSpec as an xarray dataset

        Args:
          self: this RunSpec instance

        Returns:
          xr.Dataset: An XArray dataset containing all data from the RunSpec
        """

        # Convert Runspec data to dfs
        data_dfs = to_df_helper(self)

        # Set index to columns other than "VALUE" (only for parameter dataframes)
        for df_name, df in data_dfs.items():
            if not df_name.isupper():
                data_dfs[df_name] = df.set_index(df.columns.difference(["VALUE"]).tolist())
        # Convert params to data arrays
        data_arrays = {x: y.to_xarray()["VALUE"] for x, y in data_dfs.items() if not x.isupper()}
        # Create dataset
        ds = xr.Dataset(data_vars=data_arrays)

        # If runspec not generated using otoole config yaml, use linopy defaults
        if self.defaults_otoole is None:
            default_values = defaults.otoole_name_defaults
            # If storage technologies present, use additional relevant default values
            if self.storage_technologies:
                default_values = {**default_values, **defaults.otoole_name_storage_defaults}
            # Extract defaults data from OSeMOSYSData objects
            for name, osemosys_data in default_values.items():
                default_values[name] = osemosys_data.data
        # Otherwise take defaults from otoole config yaml file
        else:
            default_values = {}
            for name, data in self.defaults_otoole.values.items():
                if data["type"] == "param":
                    default_values[name] = data["default"]

        # Replace any nan values in ds with default values (or None) for corresponding param,
        # adding default values as attribute of each data array
        for name in ds.data_vars.keys():
            # Replace nan values with default values if available
            if name in default_values.keys():
                ds[name].attrs["default"] = default_values[name]
                ds[name] = ds[name].fillna(default_values[name])
            # Replace all other nan values with None
            # TODO: remove this code if nan values wanted in the ds
            # else:
            #    ds[name].attrs["default"] = None
            #    ds[name] = ds[name].fillna(None)

        return ds

    @classmethod
    def from_otoole_csv(cls, root_dir, id: str | None = None):
        dfs = {}
        otoole_cfg = OtooleCfg(empty_dfs=[])
        for key in list(cls.otoole_stems):
            try:
                dfs[key] = pd.read_csv(Path(root_dir) / f"{key}.csv")
                if dfs[key].empty:
                    otoole_cfg.empty_dfs.append(key)
            except FileNotFoundError:
                otoole_cfg.empty_dfs.append(key)

        # load from other objects
        impacts = Impact.from_otoole_csv(root_dir=root_dir)
        regions = Region.from_otoole_csv(root_dir=root_dir)
        technologies = Technology.from_otoole_csv(root_dir=root_dir)
        storage_technologies = TechnologyStorage.from_otoole_csv(root_dir=root_dir)
        commodities = Commodity.from_otoole_csv(root_dir=root_dir)
        time_definition = TimeDefinition.from_otoole_csv(root_dir=root_dir)

        # read in depreciation_method and replace enum
        if "DepreciationMethod" not in otoole_cfg.empty_dfs:
            dfs["DepreciationMethod"]["VALUE"] = dfs["DepreciationMethod"]["VALUE"].map(
                {1: "sinking-fund", 2: "straight-line"}
            )
            depreciation_method = dfs["DepreciationMethod"].set_index("REGION")["VALUE"].to_dict()
        else:
            depreciation_method = None

        # discount rate from data
        discount_rate = (
            dfs["DiscountRate"].set_index("REGION")["VALUE"].to_dict()
            if "DiscountRate" not in otoole_cfg.empty_dfs
            else None
        )
        if "DiscountRateIdv" not in otoole_cfg.empty_dfs:
            discount_rate_idv = group_to_json(
                g=dfs["DiscountRateIdv"],
                root_column=None,
                data_columns=["REGION", "TECHNOLOGY"],
                target_column="VALUE",
            )
        else:
            discount_rate_idv = None

        # merge with Idv if necessary or just take discount_rate_idv
        if discount_rate is not None and discount_rate_idv is not None:
            # merge together
            discount_rate = {k: {"*": v} for k, v in discount_rate.items()}
            discount_rate = merge(discount_rate, discount_rate_idv)
        elif discount_rate is None and discount_rate_idv is not None:
            discount_rate = discount_rate_idv

        # reserve margin and renewable production target
        reserve_margin = (
            group_to_json(
                g=dfs["ReserveMargin"],
                root_column=None,
                data_columns=["REGION", "YEAR"],
                target_column="VALUE",
            )
            if "ReserveMargin" not in otoole_cfg.empty_dfs
            else None
        )
        renewable_production_target = (
            group_to_json(
                g=dfs["REMinProductionTarget"],
                root_column=None,
                data_columns=["REGION", "YEAR"],
                target_column="VALUE",
            )
            if "REMinProductionTarget" not in otoole_cfg.empty_dfs
            else None
        )

        if "RETagFuel" not in otoole_cfg.empty_dfs:
            dfs["RETagFuel"]["VALUE"] = dfs["RETagFuel"]["VALUE"].map({0: False, 1: True})
            re_tagfuel_data = group_to_json(
                g=dfs["RETagFuel"],
                root_column=None,
                data_columns=["FUEL", "REGION", "YEAR"],
                target_column="VALUE",
            )
            for commodity in commodities:
                if commodity.id in re_tagfuel_data.keys():
                    commodity.include_in_joint_renewable_target = OSeMOSYSData.RY.Bool(
                        re_tagfuel_data[commodity.id]
                    )

        if "RETagTechnology" not in otoole_cfg.empty_dfs:
            dfs["RETagTechnology"]["VALUE"] = dfs["RETagTechnology"]["VALUE"].map(
                {0: False, 1: True}
            )
            re_tagtechnology_data = group_to_json(
                g=dfs["RETagTechnology"],
                root_column=None,
                data_columns=["TECHNOLOGY", "REGION", "YEAR"],
                target_column="VALUE",
            )
            for technology in technologies:
                if technology.id in re_tagtechnology_data.keys():
                    technology.include_in_joint_renewable_target = OSeMOSYSData.RY.Bool(
                        re_tagtechnology_data[technology.id]
                    )

        if "ReserveMarginTagFuel" not in otoole_cfg.empty_dfs:
            dfs["ReserveMarginTagFuel"]["VALUE"] = dfs["ReserveMarginTagFuel"]["VALUE"].map(
                {0: False, 1: True}
            )
            reserve_margin_fuel_data = group_to_json(
                g=dfs["ReserveMarginTagFuel"],
                root_column=None,
                data_columns=["FUEL", "REGION", "YEAR"],
                target_column="VALUE",
            )
            for commodity in commodities:
                if commodity.id in reserve_margin_fuel_data.keys():
                    commodity.include_in_joint_reserve_margin = OSeMOSYSData.RY.Bool(
                        reserve_margin_fuel_data[commodity.id]
                    )

        if "ReserveMarginTagTechnology" not in otoole_cfg.empty_dfs:
            dfs["ReserveMarginTagTechnology"]["VALUE"] = dfs["ReserveMarginTagTechnology"][
                "VALUE"
            ].map({0: False, 1: True})
            reserve_margin_technology_data = group_to_json(
                g=dfs["ReserveMarginTagTechnology"],
                root_column=None,
                data_columns=["TECHNOLOGY", "REGION", "YEAR"],
                target_column="VALUE",
            )
            for technology in technologies:
                if technology.id in reserve_margin_technology_data.keys():
                    technology.include_in_joint_reserve_margin = OSeMOSYSData.RY.Bool(
                        reserve_margin_technology_data[technology.id]
                    )

        return cls(
            id=id if id else Path(root_dir).name,
            discount_rate=discount_rate,
            depreciation_method=depreciation_method,
            reserve_margin=reserve_margin,
            renewable_production_target=renewable_production_target,
            impacts=impacts,
            regions=regions,
            technologies=technologies,
            storage_technologies=storage_technologies,
            commodities=commodities,
            time_definition=time_definition,
            otoole_cfg=otoole_cfg,
        )

    def to_otoole_csv(self, output_directory):
        """
        Convert Runspec to otoole style output CSVs and config.yaml

        Parameters
        ----------
        output_directory: str
            Path to the output directory for CSV files to be placed
        """

        # do subsidiary objects
        Technology.to_otoole_csv(technologies=self.technologies, output_directory=output_directory)
        TechnologyStorage.to_otoole_csv(
            storage_technologies=self.storage_technologies, output_directory=output_directory
        )
        Impact.to_otoole_csv(impacts=self.impacts, output_directory=output_directory)
        Commodity.to_otoole_csv(commodities=self.commodities, output_directory=output_directory)
        Region.to_otoole_csv(regions=self.regions, output_directory=output_directory)
        self.time_definition.to_otoole_csv(output_directory=output_directory)

        # collect dataframes
        dfs = {}

        # depreciation_method
        if self.depreciation_method:
            df = pd.json_normalize(self.depreciation_method.data).T.rename(columns={0: "VALUE"})
            df[["REGION"]] = pd.DataFrame(df.index.str.split(".").to_list(), index=df.index)
            df["VALUE"] = df["VALUE"].map({"sinking-fund": 1, "straight-line": 2})
            dfs["DepreciationMethod"] = df

        # discount rate
        if self.discount_rate:
            df = pd.json_normalize(self.discount_rate.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "TECHNOLOGY"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            # if there are different discount rates per technology, use Idv
            if (df.groupby(["REGION"])["VALUE"].nunique() > 1).any():
                idv_regions = (df.groupby(["REGION"])["VALUE"].nunique() > 1).index
                dfs["DiscountRateIdv"] = df.loc[df["REGIONS"].isin(idv_regions)]
                dfs["DiscountRate"] = df.loc[~df["REGIONS"].isin(idv_regions)].drop(
                    columns=["TECHNOLOGY"]
                )
            else:
                dfs["DiscountRate"] = df.drop(columns=["TECHNOLOGY"])

        # reserve margins
        if self.reserve_margin:
            df = pd.json_normalize(self.reserve_margin.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "YEAR"]] = pd.DataFrame(df.index.str.split(".").to_list(), index=df.index)
            dfs["ReserveMargin"] = df

            dfs_tag_technology = []
            for technology in self.technologies:
                if technology.include_in_joint_reserve_margin is not None:
                    df = pd.json_normalize(
                        technology.include_in_joint_reserve_margin.data
                    ).T.rename(columns={0: "VALUE"})
                    df["TECHNOLOGY"] = technology.id
                    df[["REGION", "YEAR"]] = pd.DataFrame(
                        df.index.str.split(".").to_list(), index=df.index
                    )
                    df["VALUE"] = df["VALUE"].astype(int)
                    dfs_tag_technology.append(df)

            dfs_tag_fuel = []
            for commodity in self.commodities:
                if commodity.include_in_joint_reserve_margin is not None:
                    df = pd.json_normalize(commodity.include_in_joint_reserve_margin.data).T.rename(
                        columns={0: "VALUE"}
                    )
                    df["FUEL"] = commodity.id
                    df[["REGION", "YEAR"]] = pd.DataFrame(
                        df.index.str.split(".").to_list(), index=df.index
                    )
                    df["VALUE"] = df["VALUE"].astype(int)
                    dfs_tag_fuel.append(df)

            dfs["ReserveMarginTagTechnology"] = pd.concat(dfs_tag_technology)
            dfs["ReserveMarginTagFuel"] = pd.concat(dfs_tag_fuel)

        # min renewable production targets
        if self.renewable_production_target:
            df = pd.json_normalize(self.renewable_production_target.data).T.rename(
                columns={0: "VALUE"}
            )
            df[["REGION", "YEAR"]] = pd.DataFrame(df.index.str.split(".").to_list(), index=df.index)
            dfs["REMinProductionTarget"] = df

            dfs_tag_technology = []
            for technology in self.technologies:
                if technology.include_in_joint_renewable_target is not None:
                    df = pd.json_normalize(
                        technology.include_in_joint_renewable_target.data
                    ).T.rename(columns={0: "VALUE"})
                    df["TECHNOLOGY"] = technology.id
                    df[["REGION", "YEAR"]] = pd.DataFrame(
                        df.index.str.split(".").to_list(), index=df.index
                    )
                    df["VALUE"] = df["VALUE"].astype(int)
                    dfs_tag_technology.append(df)

            dfs_tag_fuel = []
            for commodity in self.commodities:
                if commodity.include_in_joint_renewable_target is not None:
                    df = pd.json_normalize(
                        commodity.include_in_joint_renewable_target.data
                    ).T.rename(columns={0: "VALUE"})
                    df["FUEL"] = commodity.id
                    df[["REGION", "YEAR"]] = pd.DataFrame(
                        df.index.str.split(".").to_list(), index=df.index
                    )
                    df["VALUE"] = df["VALUE"].astype(int)
                    dfs_tag_fuel.append(df)

            dfs["RETagTechnology"] = pd.concat(dfs_tag_technology)
            dfs["RETagFuel"] = pd.concat(dfs_tag_fuel)

        # write dataframes
        for stem, _params in self.otoole_stems.items():
            if stem not in self.otoole_cfg.empty_dfs:
                dfs[stem].to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)
