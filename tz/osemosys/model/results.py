from linopy import Model as LPModel


class Results:

    def __init__(
            self, 
            linopy_model: LPModel
        ):

        self._m = linopy_model

        # append results singular
        self.NewCapacity = self._m["NewCapacity"].solution.to_dataframe()

        # append results in loop
        for var_name in self._m.variables:

            setattr(
                self, 
                var_name, 
                self._m[var_name].solution.to_dataframe()
            )