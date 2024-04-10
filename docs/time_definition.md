# TimeDefinition

The TimeDefinition class contains all temporal data needed for an OSeMOSYS model. There are
multiple pathways to creating a TimeDefinition object, where any missing information is
inferred from the data provided.

Only a single instance of TimeDefinition is needed to run a model and, as a minimum, only
`years` need to be provided to create a TimeDefinition object.

The other parameters corresponding to the OSeMOSYS time related sets (`seasons`, `timeslices`,
`day_types`, `daily_time_brackets`) can be provided as lists or ranges.

One parameter additional to those correponsding to OSeMOSYS parameters is used , `adj`,
which specified the adjency matrices for `years`, `seasons`, `day_types`,
`daily_time_brackets`, `timeslices`. If not providing values for `adj`, it is assumed that
the other variables are provided in order from first to last. If providing the values directly,
these can be provided as a dict, an example of which for years and timeslices is below:

```python
adj = {
    "years": dict(zip(range(2020, 2050), range(2021, 2051))),
    "timeslices": {"A": "B", "B": "C", "C": "D"},
}
```

### Pathway 1 - Construction from years only

If only `years` are provided, the remaining necessary temporal parameters (`seasons`,
`day_types`, `daily_time_brackets`) are assumed to be singular.

### Pathway 2 - Construction from parts

If no timeslice data is provided, but any of the below is, it is used to construct timeslices:
    - seasons
    - daily_time_brackets
    - day_types
    - year_split
    - day_split
    - days_in_day_type

### Pathway 3 - Construction from timeslices

If timeslices are provided via any of the below parameters, this is used to construct the
TimeDefinition object:
    - timeslices
    - timeslice_in_timebracket
    - timeslice_in_daytype
    - timeslice_in_season


## Parameters

`id` `(str)`: Any value may be provided for the single TimeDefintion instance.
Required parameter.

`years` `(List[int] | range(int)) | int`: OSeMOSYS YEARS. Required parameter.

`seasons` `(List[int | str]) | int`: OSeMOSYS SEASONS.
Optional, constructed if not provided.

`timeslices` `(List[int | str]) | int`: OSeMOSYS TIMESLICES.
Optional, constructed if not provided.

`day_types` `(List[int | str]) | int`: OSeMOSYS DAYTYPES.
Optional, constructed if not provided.

`daily_time_brackets` `(List[int | str])`: OSeMOSYS DAILYTIMEBRACKETS.
Optional, constructed if not provided.

`year_split` `({timeslice:{year:float}})`: OSeMOSYS YearSplit.
Optional, constructed if not provided.

`day_split` `({daily_time_bracket:{year:float}})`: OSeMOSYS DaySplit.
Optional, constructed if not provided.

`days_in_day_type` `({season:{day_type:{year:int}}})`: OSeMOSYS DaysInDayType.
Optional, constructed if not provided.

`timeslice_in_timebracket` `({timeslice:daily_time_bracket})`: OSeMOSYS Conversionlh.
Optional, constructed if not provided.

`timeslice_in_daytype` `({timeslice:day_type})`: OSeMOSYS Conversionld.
Optional, constructed if not provided.

`timeslice_in_season` `({timeslice:season})`: OSeMOSYS Conversionls.
Optional, constructed if not provided.

`adj` `({str:dict})`: Parameter to manually define adjanecy for `years`, `seasons`,
`day_types`, `daily_time_brackets`, and `timeslices`. Optional, if not providing values for
`adj`, it is assumed that the other variables are provided in order from first to last.

## Examples

Examples are given below of how a TimeDefinition object might be created using the different
pathways.

### Pathway 1 - Construction from years only

```python
from tz.osemosys.schemas.time_definition import TimeDefinition

basic_time_definition = dict(
    id="pathway_1",
    years=[2021, 2022, 2023],
)

TimeDefinition(**basic_time_definition)
```

### Pathway 2 - Construction from parts

```python
from tz.osemosys.schemas.time_definition import TimeDefinition

basic_time_definition = dict(
    id="pathway_2",
    years=range(2020, 2051),
    seasons=["winter", "summer"],
    daily_time_brackets=["morning", "day", "evening", "night"],
)

TimeDefinition(**basic_time_definition)
```

### Pathway 3 - Construction from timeslices

```python
from tz.osemosys.schemas.time_definition import TimeDefinition

basic_time_definition = dict(
    id="pathway_3",
    years=range(2020, 2051),
    timeslices=["A", "B", "C", "D"],
    adj={
        "years": dict(zip(range(2020, 2050), range(2021, 2051))),
        "timeslices": dict(zip(["A", "B", "C"], ["B", "C", "D"])),
    },
)

TimeDefinition(**basic_time_definition)
```
