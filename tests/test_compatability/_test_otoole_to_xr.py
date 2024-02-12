from feo.osemosys.schemas import RunSpec

root_dir = "data/model_three/"

run_spec_object = RunSpec.from_otoole_csv(root_dir=root_dir)

ds = run_spec_object.to_xr_ds()

print(ds)
