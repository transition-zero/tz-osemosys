from linopy import Model as LPModel


class Results:

    def __init__(
            self, 
            linopy_model: LPModel
        ):

        # save results data
        self.results_tables = list(linopy_model.variables)

        # append results singular
        self.NewCapacity = linopy_model["NewCapacity"].solution.to_dataframe()

        # append results in loop
        for var_name in list(self.results_tables):

            setattr(
                self, 
                var_name, 
                linopy_model[var_name].solution.to_dataframe()
            )