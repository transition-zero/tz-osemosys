import xarray as xr
from linopy import Model as LPModel
from linopy import available_solvers

from tz.osemosys.io.load_model import load_cfg
from tz.osemosys.model.constraints import add_constraints
from tz.osemosys.model.objective import add_objective
from tz.osemosys.model.variables import add_variables
from tz.osemosys.schemas import RunSpec


class Model(RunSpec):
    _data: xr.Dataset
    _m: LPModel

    @classmethod
    def from_yaml(cls, *spec_files):
        cfg = load_cfg(*spec_files)
        return cls(**cfg)

    def _build_dataset(self):
        data = self.to_xr_ds()
        return data

    def _build_model(self):
        m = LPModel(force_dim_names=True)
        m = add_variables(self._data, m)
        m = add_constraints(self._data, m)
        m = add_objective(m)
        return m

    def _build(self):
        self._data = self._build_dataset()

        self._m = self._build_model()
        return True

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

        return True
