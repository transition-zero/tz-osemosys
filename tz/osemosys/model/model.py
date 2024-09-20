from typing import Any, Dict, Optional

import xarray as xr
from linopy import LinearExpression
from linopy import Model as LPModel
from linopy import available_solvers

from tz.osemosys.io.load_model import load_cfg
from tz.osemosys.model.constraints import add_constraints
from tz.osemosys.model.linear_expressions import add_linear_expressions
from tz.osemosys.model.objective import add_objective
from tz.osemosys.model.solution import build_solution
from tz.osemosys.model.variables import add_variables
from tz.osemosys.schemas import RunSpec


class Model(RunSpec):
    """
    # Model

    The Model class contains all data required to run a TZ-OSeMOSYS model, spread across subclasses,
    along with class methods for loading/constructing and solving a model.

    ## Parameters

    `id` `(str)`: Used to represent the name of the OSeMOSYS model.
    Required parameter.

    `time_definition` `(TimeDefinition)` - Single TimeDefinition class instance to contain all
    temporal data related to the model. Required parameter.

    `regions` `(List[Region])` - List of Region instances to contain region names.
    Required parameter.

    `commodities` `(List[Commodity])` - List of Commodity instances to contain all data related to
    commodities (OSeMOSYS FUEL).
    Required parameter.

    `impacts` `(List[Impact])` - List of Impact instances to contain all data related to impacts
    (OSeMOSYS EMISSION).
    Required parameter.

    `technologies` `(List[Technology])` - List of Technology instances to contain all data
    related to technologies.
    Required parameter.

    `storage` `(List[Storage])` - List of Storage instances to contain all data related to storage.
    Optional parameter, defaults to `None`.

    `trade` `(List[Trade])` - List of Trade instances to contain all data related to trade routes.
    Optional parameter, defaults to `None`.

    `depreciation_method` `({region:str})` - OSeMOSYS DepreciationMethod.
    Parameter defining the type of depreciation to be applied, must take values of 'sinking-fund' or
    'straight-line'.
    Optional parameter, defaults to 'sinking-fund'.

    `discount_rate` `({region:float})` - OSeMOSYS DiscountRate.
    Region specific value for the discount rate.
    Optional parameter, defaults to 0.05.

    `cost_of_capital` `({region:{technology:float}})` - OSeMOSYS DiscountRateIdv.
    Discount rate specified by region and technology.
    Optional parameter, defaults to `None`.

    `cost_of_capital_storage` `({region:{storage:float}})` - OSeMOSYS DiscountRateStorage.
    Discount rate specified by region and storage.
    Optional parameter, defaults to `None`.

    `cost_of_capital_trade` `({region:{region:{commodity:float}}})` - Parameter additional to
    OSeMOSYS base variables. Discount rate specified for trade (transmission) technologies.
    Optional parameter, defaults to `None`.

    `reserve_margin` `({region:{year:float}})` - OSeMOSYS ReserveMargin.
    Minimum level of the reserve margin required to be provided for all the tagged commodities, by
    the tagged technologies. If no reserve margin is required, the parameter will have value 1; if,
    for instance, 20% reserve margin is required, the parameter will have value 1.2.
    Optional parameter, defaults to 1.

    `renewable_production_target` `({region:{year:float}})` - OSeMOSYS REMinProductionTarget.
    Minimum ratio of all renewable commodities tagged in the
    include_in_joint_renewable_target parameter, to be
    produced by the technologies tagged with the include_in_joint_renewable_target parameter.
    Optional parameter, defaults to `None`.

    ## Loading/constructing a model

    ### From dicts

    A simple example of how a Model object might be created directly from provided data is below:

    ```python
    from tz.osemosys import (
        Model,
        Technology,
        TimeDefinition,
        Commodity,
        Region,
        Impact,
        OperatingMode,
    )

    time_definition = TimeDefinition(id="years-only", years=range(2020, 2051))
    regions = [Region(id="single-region")]
    commodities = [Commodity(id="electricity", demand_annual=25 * 8760)]  # 25GW * 8760hr/yr
    impacts = [Impact(id="CO2", penalty=60)]  # 60 $mn/Mtonne
    technologies = [
        Technology(
            id="coal-gen",
            operating_life=40,  # years
            capex=800,  # mn$/GW
            # straight-line reduction to 2040
            residual_capacity={
                yr: 25 * max((1 - (yr - 2020) / (2040 - 2020), 0))
                for yr in range(2020, 2051)
            },
            operating_modes=[
                OperatingMode(
                    id="generation",
                    # $mn20/Mt.coal / 8.14 TWh/Mt coal * 8760 GWh/GW / 0.3 /1000 GWh/TWh (therm eff)
                    opex_variable=20 / 8.14 * 8760 / 0.3 / 1000,  # $71/GW/yr
                    output_activity_ratio={"electricity": 1.0 * 8760},  # GWh/yr/GW
                    emission_activity_ratio={
                        "CO2": 0.354 * 8760 / 1000
                    },  # Mtco2/TWh * 8760GWh/Gw/yr /1000 GWh/TWh
                )
            ],
        ),
        Technology(
            id="solar-pv",
            operating_life=25,
            capex=1200,
            capacity_factor=0.3,
            operating_modes=[
                OperatingMode(
                    id="generation",
                    opex_variable=0,
                    output_activity_ratio={"electricity": 1.0 * 8760},  # GWh/yr/GW
                )
            ],
        ),
    ]

    model = Model(
        id="simple-carbon-price",
        time_definition=time_definition,
        regions=regions,
        commodities=commodities,
        impacts=impacts,
        technologies=technologies,
    )
    ```
    ### From csv

    A Model object can also be created from a set of otoole style CSVs as below, using the class
    method from_otoole_csv():

    ```python
    from tz.osemosys import Model

    path_to_csvs = "examples/otoole_compat/input_csv/otoole-full-electricity-complete/"

    model = Model.from_otoole_csv(root_dir=path_to_csvs)
    ```

    ### From yaml

    Alternatively, a model can be created from a TZ-OSeMOSYS yaml or set of yamls, examples of
    which can be found in the tz-osemosys repository.

    ```python
    from tz.osemosys import Model

    path_to_yaml = "examples/utopia/main.yaml"

    model = Model.from_yaml(path_to_yaml)
    ```

    ## Solving a model

    Once a model object has been constructed or loaded via one of the above methods, it can be
    solved by calling the solve() method.

    ```python
    from tz.osemosys import Model

    path_to_yaml = "examples/utopia/main.yaml"

    model = Model.from_yaml(path_to_yaml)

    model.solve()
    ```

    By default, the model will be solved using the first available solver in the list of available
    solvers. To specify a solver, pass the name of the solver as a string to the solve() method for
    the argument `solver` (e.g. `model.solve(solver="highs")`).

    ### Viewing the model solution

    Once the model has been solved, the solution can be accessed via the `solution` attribute of the
    model object, which returns an xarray DataSet.

    To display all available solution DataArrays within the solution DataSet, run:
    ```python
    model.solution.data_vars
    ```

    To view the values of a specific DataArray, such as NewCapacity, run:
    ```python
    model.solution["NewCapacity"]
    ```

    This can be converted to a more easily readible format by converting to a pandas DataFrame:
    ```python
    model.solution["NewCapacity"].to_dataframe().reset_index()
    ```

    ### Writing the model solution to excel

    Writing a specfic DataArray (NewCapacity) to an excel file can be done by running the following:
    ```python
    model.solution["NewCapacity"].to_dataframe().reset_index().to_excel(
        "NewCapacity.xlsx", index=False
    )
    ```

    All DataArrays in the model solution can be written to excel files by running the following:
    ```python
    for array in model.solution:
        model.solution[array].to_dataframe().reset_index().to_excel(
            f"{array}.xlsx", index=False
        )
    ```

    """

    _data: xr.Dataset
    _m: LPModel
    _linear_expressions: Dict[str, LinearExpression]
    _solution: Optional[xr.Dataset] = None
    _objective: Optional[float] = None
    _objective_constant: Optional[float] = None

    @classmethod
    def from_yaml(cls, *spec_files):
        cfg = load_cfg(*spec_files)
        return cls(**cfg)

    @classmethod
    def from_otoole_csv(cls, root_dir, id: str | None = None):
        runspec = RunSpec.from_otoole_csv(root_dir, id)
        cfg = {name: data for name, data in runspec}
        return cls(**cfg)

    def _build_dataset(self):
        data = self.to_xr_ds()
        return data

    def _build_model(self):
        self._m = LPModel(force_dim_names=True)
        add_variables(self._data, self._m)
        self._linear_expressions = add_linear_expressions(self._data, self._m)
        add_constraints(self._data, self._m, self._linear_expressions)
        self._objective_constant = add_objective(self._m, self._linear_expressions)

    def _build(self):
        self._data = self._build_dataset()
        self._build_model()

    def _get_solution(self, solution_vars: list[str] | str | None = None):
        return build_solution(self._m, self._linear_expressions, solution_vars)

    def solve(
        self,
        solver: str | None = None,
        lp_path: str | None = None,
        solution_vars: list[str] | str | None = None,
        **linopy_solve_kwargs: Any,
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

        self._m.solve(solver_name=solver, **linopy_solve_kwargs)

        if self._m.termination_condition == "optimal":
            self._solution = self._get_solution(solution_vars)

            # rather hacky - constants not currently supported in objective functions:
            # https://github.com/PyPSA/linopy/issues/236
            # TODO: find out why and add constant back on: + self._objective_constant
            self._objective = self._solution.TotalDiscountedCost.sum().values

        return self._m.status

    @property
    def solution(self):
        return self._solution

    @property
    def objective(self):
        if not self._objective:
            raise ValueError("Model has not been solved yet or the solution is not optimal.")
        return self._objective
