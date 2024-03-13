# Example Models

This folder provides a number of example models using the tz-osemosys framework.

## [**utopia**](./utopia/)

Utopia is the OSeMOSYS 'hello world' model - a whole-energy system model for the fictional region of 'Utopia'. It has primary energy, energy transformation, and final energy technologies, as well as two types of emissions - NOx and CO2. The model is configured to run for 31 years from 1990 to 2020, and has 6 timeslices composed of three seasons and two dayparts - night and day.

## [**utopia-2-region**](./utopia-2-region/)

This model extends the Utopia model to two regions. Investible energy storage and transmission options are also included. **To be completed**

## [**CAISO-ERCOT-IC**](./CAISO-ERCOT-IC/)

This is a four-region model illustrating interconnector feasibility in the SouthWest United States, between California (CAISO) and Texas (ERCOT). The regions have differing access to indigenous renewable resources and offshore fossil fuel resources.


## [**otoole compatability - simple-hydro**](./otoole_compat/input_csv/otoole-simple-hydro/)

This is a simple osemosys model of hydropower and contains only 3 technologies:

- MINE_WATER - which produces the WATER resource used as an input to...
- HYDRO - a modelled hydropower plant, taking WATER as an input and outputtting electricity
- TRANSMISSION - modelled transmission taking the electricity output of HYDRO and converting into the final electricity demand

The model runs from 2020 to 2070, with 8 timeslices.

## [**otoole compatability - electricity**](./otoole_compat/input_csv/otoole-full-electricity/)

This model has only one final electricity demand like the previous, but contains several more pathways to meet the demand, including fossil fuel and renewable technologies.

Again the model runs from 2020 to 2070, with 8 timeslices, and although being more complicated than the previously mentioned model, is again only used for workflow testing.

## [**otoole compatability - electricity-complete**](./otoole_compat/input_csv/otoole-full-electricity-complete/)

This model uses the entire otoole suite of csv inputs (including storage), allowing validation of the complete csv composition round-trip.
