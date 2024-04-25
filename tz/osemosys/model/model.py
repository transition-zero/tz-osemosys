from typing import Dict

import xarray as xr
from linopy import LinearExpression
from linopy import Model as LPModel
from linopy import available_solvers

from tz.osemosys.io.load_model import load_cfg
from tz.osemosys.model.constraints import add_constraints
from tz.osemosys.model.linear_expressions import add_linear_expressions
from tz.osemosys.model.objective import add_objective
from tz.osemosys.model.variables import add_variables
from tz.osemosys.model.results import Results
from tz.osemosys.schemas import RunSpec

class Model(RunSpec):
    _data: xr.Dataset
    _m: LPModel
    _linear_expressions: Dict[str, LinearExpression]

    @classmethod
    def from_yaml(cls, *spec_files):
        cfg = load_cfg(*spec_files)
        return cls(**cfg)

    def _build_dataset(self):
        data = self.to_xr_ds()
        return data

    def _build_model(self):
        self._m = LPModel(force_dim_names=True)
        add_variables(self._data, self._m)
        self._linear_expressions = add_linear_expressions(self._data, self._m)
        add_constraints(self._data, self._m, self._linear_expressions)
        add_objective(self._m)

    def _build(self):
        self._data = self._build_dataset()
        self._build_model()

    def solve(
        self,
        solver: str | None = None,
        lp_path: str | None = None,
        io_api: str = "lp",
        log_fn: str | None = None,
    ):
        self._build()

        if solver is None:
            solver = available_solvers[0]
        else:
            assert (
                solver in available_solvers
            ), f"Solver {solver} not available. Choose from {available_solvers}."

        if lp_path:
            self._m.to_file(lp_path)

        self._m.solve(solver_name=solver, io_api=io_api, log_fn=log_fn)

        if self._m.termination_condition == "optimal":
            self._results = Results(self._m)

        return True

    @property
    def results(self):
        return self._results