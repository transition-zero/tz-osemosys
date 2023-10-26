




class Impact(OSeMOSYSBase):
    # previously 'emissions'
    constraint: Union[RegionTechnologyYearData, YearData]
    exogenous: Union[RegionTechnologyYearData, YearData]
    penalty: RegionTechnologyYearData