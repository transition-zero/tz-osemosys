# Example data
<!-- Badges Begin -->

<!-- Badges End -->


This folder contains example data which can be used to create and run a model with TZ osemosys.

It contains the following subfolders:
- CAISO-ERCOT-IC - example yaml files which can be used to run TZ osemosys via the from_minspec route
- otoole_config_files - otoole config files, which can optionally be used in the from_csv route to set one's own default values
- otoole_csvs - 2 sets of CSV files, which can be used to run TZ osemosys via the from_csv route

Within otoole_config_files and otoole_csvs sit 2 different models, otoole-simple-hydro and otoole-full-electricity, which are explained in more detail below.


## otoole-simple-hydro

This is a simple osemosys model of hydropower and contains only 3 technologies:

- MINE_WATER - which produces the WATER resource used as an input to...
- HYDRO - a modelled hydropower plant, taking WATER as an input and outputtting electricity
- TRANSMISSION - modelled transmission taking the electricity output of HYDRO and converting into the final electricity demand

The model runs from 2020 to 2070, with 8 timeslices.

Due to it's simplicity, this model is only used in testing of TZ osemosys workflows.

## otoole-full-electricity

This model has only one final electricity demand like the previous, but contains several more pathways to meet the demand, including fossil fuel and renewable technologies.

Again the model runs from 2020 to 2070, with 8 timeslices, and although being more complicated than the previously mentioned model, is again only used for workflow testing.
