from feo.osemosys import schemas


def adapter(spec: schemas.RunSpec):
    # where the RunSpec instance actually get's changed to linopy model via an xr ds
