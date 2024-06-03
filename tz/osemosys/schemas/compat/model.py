import os
from pathlib import Path
from typing import ClassVar, Dict, Union

import pandas as pd
import xarray as xr
from pydantic import BaseModel, Field

from tz.osemosys.defaults import defaults, defaults_linopy
from tz.osemosys.schemas.base import OSeMOSYSData
from tz.osemosys.schemas.commodity import Commodity
from tz.osemosys.schemas.compat.base import DefaultsOtoole, OtooleCfg
from tz.osemosys.schemas.impact import Impact
from tz.osemosys.schemas.region import Region
from tz.osemosys.schemas.storage import Storage
from tz.osemosys.schemas.technology import Technology
from tz.osemosys.schemas.time_definition import TimeDefinition
from tz.osemosys.schemas.trade import Trade
from tz.osemosys.schemas.validation.timedefinition_validation import time_adj_to_list
from tz.osemosys.utils import flatten, group_to_json


class RunSpecOtoole(BaseModel):
    """
    Class to contain methods for converting Runspec data to and from otoole style CSVs,
    and to xarray for use in linopy
    """

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
            "attribute": "cost_of_capital",
            "columns": ["REGION", "TECHNOLOGY", "VALUE"],
        },
        "DiscountRateStorage": {
            "attribute": "cost_of_capital_storage",
            "columns": ["REGION", "STORAGE", "VALUE"],
        },
    }

    def map_datatypes(self, df: pd.DataFrame):
        index_cols = df.index.names
        df = df.reset_index()
        for c in df.columns:
            if c == "YEAR":
                df[c] = df[c].astype(int)
            elif c != "VALUE":
                df[c] = df[c].astype(str)
        df = df.set_index(index_cols)
        return df

    def to_xr_ds(self):
        """
        Return the current RunSpec as an xarray dataset

        Args:
          self: this RunSpec instance

        Returns:
          xr.Dataset: An XArray dataset containing all data from the RunSpec
        """

        # Convert Runspec data to dfs
        data_dfs = self.to_dataframes()

        # cast any YEAR to year
        for _df_name, df in data_dfs.items():
            if "YEAR" in df.columns:
                df["YEAR"] = df["YEAR"].astype(int)

        # Set index to columns other than "VALUE" (only for parameter dataframes)
        for df_name, df in data_dfs.items():
            if not df_name.isupper():
                data_dfs[df_name] = df.set_index(df.columns.difference(["VALUE"]).tolist())

        for obj in Impact, Technology, Commodity, TimeDefinition, Trade, self:
            for stem, params in obj.otoole_stems.items():
                if stem not in data_dfs.keys():
                    data_dfs[stem] = pd.DataFrame(columns=params["columns"]).set_index(
                        [c for c in params["columns"] if c != "VALUE"]
                    )

        # Convert params to data arrays
        data_arrays = {
            var_name: self.map_datatypes(df).to_xarray()["VALUE"]
            for var_name, df in data_dfs.items()
            if not var_name.isupper()
        }

        coords = {
            var_name: df["VALUE"].astype(str).tolist()
            for var_name, df in data_dfs.items()
            if var_name.isupper() and var_name != "YEAR"
        }
        coords["YEAR"] = data_dfs["YEAR"]["VALUE"].astype(int).tolist()

        # Order seasons/day_types/time_brackets chronologically by adjacency if provided
        if coords["SEASON"] and self.time_definition.adj.seasons:
            coords["SEASON"] = time_adj_to_list(self.time_definition.adj.seasons)
        if coords["DAYTYPE"] and self.time_definition.adj.day_types:
            coords["DAYTYPE"] = time_adj_to_list(self.time_definition.adj.day_types)
        if coords["DAILYTIMEBRACKET"] and self.time_definition.adj.time_brackets:
            coords["DAILYTIMEBRACKET"] = time_adj_to_list(self.time_definition.adj.time_brackets)

        ds = xr.Dataset(data_vars=data_arrays, coords=coords)

        # If runspec not generated using otoole config yaml, use linopy defaults
        if self.defaults_otoole is None:
            default_values = defaults_linopy.otoole_name_defaults
            # If storage technologies present, use additional relevant default values
            if self.storage:
                default_values = {**default_values, **defaults_linopy.otoole_name_storage_defaults}
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
        storage = Storage.from_otoole_csv(root_dir=root_dir)
        commodities = Commodity.from_otoole_csv(root_dir=root_dir)
        time_definition = TimeDefinition.from_otoole_csv(root_dir=root_dir)
        trade = Trade.from_otoole_csv(root_dir=root_dir)

        otoole_cfg.empty_dfs += list(
            set(flatten([impact.otoole_cfg.empty_dfs for impact in impacts]))
        )
        otoole_cfg.empty_dfs += list(
            set(flatten([technology.otoole_cfg.empty_dfs for technology in technologies]))
        )
        otoole_cfg.empty_dfs += list(
            set(flatten([commodity.otoole_cfg.empty_dfs for commodity in commodities]))
        )
        otoole_cfg.empty_dfs += list(set(time_definition.otoole_cfg.empty_dfs))

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
            cost_of_capital = group_to_json(
                g=dfs["DiscountRateIdv"],
                root_column=None,
                data_columns=["REGION", "TECHNOLOGY"],
                target_column="VALUE",
            )
        else:
            cost_of_capital = None
        if "DiscountRateStorage" not in otoole_cfg.empty_dfs:
            cost_of_capital_storage = group_to_json(
                g=dfs["DiscountRateStorage"],
                root_column=None,
                data_columns=["REGION", "STORAGE"],
                target_column="VALUE",
            )
        else:
            cost_of_capital_storage = None

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
            discount_rate=discount_rate or defaults.discount_rate,
            cost_of_capital=cost_of_capital,
            cost_of_capital_storage=cost_of_capital_storage,
            depreciation_method=depreciation_method or defaults.depreciation_method,
            reserve_margin=reserve_margin or defaults.reserve_margin,
            renewable_production_target=renewable_production_target,
            impacts=impacts,
            regions=regions,
            technologies=technologies,
            storage=storage,
            commodities=commodities,
            time_definition=time_definition,
            trade=trade,
            otoole_cfg=otoole_cfg,
        )

    def to_model_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        Convert RunSpec to otoole style output CSVs, only for parameters created on the model object
        """

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
            df[["REGION"]] = pd.DataFrame(df.index.str.split(".").to_list(), index=df.index)
            dfs["DiscountRate"] = df

        if self.cost_of_capital:
            df = pd.json_normalize(self.cost_of_capital.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "TECHNOLOGY"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["DiscountRateIdv"] = df

        if self.cost_of_capital_storage:
            df = pd.json_normalize(self.cost_of_capital_storage.data).T.rename(columns={0: "VALUE"})
            df[["REGION", "STORAGE"]] = pd.DataFrame(
                df.index.str.split(".").to_list(), index=df.index
            )
            dfs["DiscountRateStorage"] = df

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

            dfs["ReserveMarginTagTechnology"] = (
                pd.concat(dfs_tag_technology)
                if dfs_tag_technology
                else pd.DataFrame(
                    columns=self.otoole_stems["ReserveMarginTagTechnology"]["columns"]
                )
            )
            dfs["ReserveMarginTagFuel"] = (
                pd.concat(dfs_tag_fuel)
                if dfs_tag_fuel
                else pd.DataFrame(columns=self.otoole_stems["ReserveMarginTagFuel"]["columns"])
            )

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

        return dfs

    def to_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        Convert Runspec to otoole style output CSVs and config.yaml

        Parameters
        ----------
        output_directory: str
            Path to the output directory for CSV files to be placed
        """

        # collect dataframes
        dfs = self.to_model_dataframes()

        # do subsidiary objects
        dfs.update(Technology.to_dataframes(technologies=self.technologies))
        dfs.update(Impact.to_dataframes(impacts=self.impacts))
        dfs.update(Commodity.to_dataframes(commodities=self.commodities))
        dfs.update(Region.to_dataframes(regions=self.regions))
        dfs.update(self.time_definition.to_dataframes())
        if self.storage is not None:
            dfs.update(Storage.to_dataframes(storage=self.storage))
        if self.trade is not None:
            dfs.update(Trade.to_dataframes(trade=self.trade))

        return dfs

    def to_otoole_csv(self, output_directory):
        dfs = self.to_model_dataframes()

        # do subsidiary objects
        Technology.to_otoole_csv(technologies=self.technologies, output_directory=output_directory)
        Impact.to_otoole_csv(impacts=self.impacts, output_directory=output_directory)
        Commodity.to_otoole_csv(commodities=self.commodities, output_directory=output_directory)
        Region.to_otoole_csv(regions=self.regions, output_directory=output_directory)
        self.time_definition.to_otoole_csv(output_directory=output_directory)
        if self.storage is not None:
            Storage.to_otoole_csv(storage=self.storage, output_directory=output_directory)
        if self.trade is not None:
            Trade.to_otoole_csv(trade=self.trade, output_directory=output_directory)

        # write dataframes
        for stem, _params in self.otoole_stems.items():
            if stem not in self.otoole_cfg.empty_dfs:
                dfs[stem].to_csv(os.path.join(output_directory, f"{stem}.csv"), index=False)
