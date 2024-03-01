from typing import ClassVar

import xarray as xr
from linopy import Model

from feo.osemosys.io import load_model
from feo.osemosys.model.constraints import add_constraints
from feo.osemosys.model.variables import add_variables
from feo.osemosys.schemas import RunSpec


class Model(RunSpec):
    data: ClassVar[xr.Dataset | None] = None
    m: ClassVar[Model | None] = None

    @classmethod
    def from_yaml(cls, *spec_files):
        return load_model(*spec_files)

    def _build_dataset(self):
        data = self.to_xr_ds()
        return data

    def _build_model(self):
        m = Model(force_dim_names=True)
        m = add_variables(self.data, m)
        m = add_constraints(self.data, m)
        return m

    def _build(self):
        self.data = self._build_dataset()

        self.m = self._build_model()
        return True

    def solve(self):
        self._build()

        self.m.solve()

        return True
