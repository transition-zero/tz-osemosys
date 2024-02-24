from feo.osemosys.schemas.commodity import Commodity
from feo.osemosys.utils import recursive_keys

BASIC_COMMODITY = dict(
    id="coal",
    demand_annual=5,
    demand_profile={"*": {"0h": 0.0, "6h": 0.2, "12h": 0.3, "18h": 0.5}},
)


def test_compose_commodity():
    commodity = Commodity(**BASIC_COMMODITY)

    regions = ["R1", "R2"]
    years = [2025, 2026, 2027]
    timeslices = ["0h", "6h", "12h", "18h"]

    commodity.compose(regions=regions, years=years, timeslices=timeslices)

    demand_annual_keys = [k for k in recursive_keys(commodity.demand_annual.data)]
    for region in regions:
        assert region in [k[0] for k in demand_annual_keys]
    for year in years:
        assert str(year) in [k[1] for k in demand_annual_keys]
