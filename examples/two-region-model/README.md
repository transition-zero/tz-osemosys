# Two-region model
The two-region model (TRM) was developed to serve as a starter kit for multi-regional modelling. For example, users could use this example to develop a model for:

- Multi-country analyses.
- National-scale analyses where a country is represented at a subnational scale.

## Overview
TRM is an illustrative model for two separate regions that have an interconnected power system and shared primary fuel resources. The model schematic is illustrated below:

<img src="https://github.com/transition-zero/tz-osemosys/blob/main/examples/two-region-model/two-region-model-schematic.png" alt="" width="800" align="center">

The model captures three sources of energy: primary energy, secondary energy and final energy. As shown in the figure above, the primary energy inputs consist of:

- Domestic and imported fossil fuels (coal and gas).
- Uranium-235 for nuclear power.
- Natural resources such as solar irradiance, onshore and offshore wind, and hydrological resources.

All primary fuels are configurable and serve as feedstocks for the electricity generators in the power system.

## Model configuration

### Commodities
TRM is a multi-commodity flow model, where multiple energy carriers are represented within the optimsiation framework. Specifically, there are nine individual commodities are represented as tabulated below.

ID  | Measure
--- | ---
Coal | Primary energy
Gas | Primary energy
Solar | Primary energy
Wind (onshore) | Primary energy
Wind (offshore) | Primary energy
Uranium-235 | Primary energy
Hydrological resource | Primary energy
Primary electricity | Secondary energy
Secondary electricity | Final energy

Commodities are referenced throughout the model setup, where prices and demands of each commodities can be configured, as well as the conversion rates between commodities.

### Temporal resolution
TRM runs between 2024 and 2030 by default. Within each annual time step, there are six seasonal timeslices referred to as: ID, IN, SD, SN, WD and WN. The time definitions are defined in [`time_definitions.yaml`](https://github.com/transition-zero/tz-osemosys/blob/main/examples/two-region-model/time_definitions.yaml).

### Emissions targets
TRM does not have any emissions targets by default. However, it is setup such that emissions targets (e.g., CO2, NOx etc) can be easily implemented. Emissions targets are defined in [`targets.yaml`](https://github.com/transition-zero/tz-osemosys/blob/main/examples/two-region-model/targets.yaml).

## Running the model
Provided you have successfully setup `tz-osemosys` on your local machine as instructed, you can run the TRM model as shown below:

```python
from tz.osemosys import Model

model = Model.from_yaml("tz-osemosys/examples/two-region-model/")
model.solve()
```
