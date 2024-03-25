# TimeDefinition

The TimeDefinition class contains all temporal data needed for an OSeMOSYS model. There are
multiple pathways to creating a TimeDefinition object, where any missing information is
inferred from the data provided.

Only a single instance of TimeDefinition is needed to run a model and, as a minimum, only
`years` need to be provided to create a TimeDefinition object.

The other parameters corresponding to the OSeMOSYS time related sets (`seasons`, `timeslices`,
`day_types`, `daily_time_brackets`) can be provided as lists, ranges, or integers. If given
as integers, that many unique seasons/timeslices/day_types/daily_time_brackets will be
constructed.

### Pathway 1 - years only

If only `years` are provided, the remaining necessary temporal parameters (`seasons`,
`day_types`, `daily_time_brackets`) are assumed to be singular.

### Pathway 2 - years, seasons as int, and daily_time_brackets as int

If providing `years`, `seasons` as integers, and `daily_time_brackets` as integers, `day_types`
is assumed to be singular, and `timeslices` are constructed from the provided data.

### Pathway 3 - years, seasons, daily_time_brackets, and day_types

If providing `years`, `seasons`, `daily_time_brackets` and `day_types`, `timeslices` are
constructed from the provided data.

### Pathway 4 - years, seasons, daily_time_brackets, day_types, and timeslices

Pathway taken if providing a fully defined TimeDefinition.


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
