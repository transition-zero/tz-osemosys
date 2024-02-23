import os

import pandas as pd
import pytest


@pytest.fixture
def mock_env_var(monkeypatch):
    monkeypatch.setenv("MYVAR", "5")
    monkeypatch.setenv("MYOTHERVAR", "37")


@pytest.fixture
def create_test_model_construction_failcases():
    """
    Creates CSV sets for otoole route for failing test of model construction

    Returns: List[str] of test CSV folder locations
    """

    # Create CSV sets which fail test
    csv_data = {}
    # Read in CSV files
    for csv_file in os.listdir("examples/otoole_csvs/otoole-full-electricity"):
        if csv_file.endswith(".csv"):
            file_name = os.path.splitext(csv_file)[0]
            csv_data[file_name] = pd.read_csv(
                os.path.join("examples/otoole_csvs/otoole-full-electricity", csv_file)
            )

    # Fail - For each commodity, check there is a technology which produces it
    csv_data_edited_1 = {}
    for df_name, df in csv_data.items():
        csv_data_edited_1[df_name] = df.copy(deep=True)
    # Remove technology PWRTRNNPLXX producing final demand
    csv_data_edited_1["OutputActivityRatio"] = csv_data_edited_1["OutputActivityRatio"][
        csv_data_edited_1["OutputActivityRatio"]["TECHNOLOGY"] != "PWRTRNNPLXX"
    ]
    # Write edited CSVs
    output_folder_1 = "examples/otoole_csvs/otoole-full-electricity-edited-1"
    os.makedirs(output_folder_1, exist_ok=True)
    for df_name, df in csv_data_edited_1.items():
        df.to_csv(os.path.join(output_folder_1, f"{df_name}.csv"), index=False)

    # Fail - For each impact, check there is a technology which produces it
    csv_data_edited_2 = {}
    for df_name, df in csv_data.items():
        csv_data_edited_2[df_name] = df.copy(deep=True)
    # Remove all technologies producing impacts
    csv_data_edited_2["EmissionActivityRatio"] = csv_data_edited_2["EmissionActivityRatio"][0:0]
    # Write edited CSVs
    output_folder_2 = "examples/otoole_csvs/otoole-full-electricity-edited-2"
    os.makedirs(output_folder_2, exist_ok=True)
    for df_name, df in csv_data_edited_2.items():
        df.to_csv(os.path.join(output_folder_2, f"{df_name}.csv"), index=False)

    # Fail - For each commodity which isn't a final demand, check it is the input of a technology
    csv_data_edited_3 = {}
    for df_name, df in csv_data.items():
        csv_data_edited_3[df_name] = df.copy(deep=True)
    # Remove technology with COA as input
    csv_data_edited_3["InputActivityRatio"] = csv_data_edited_3["InputActivityRatio"][
        csv_data_edited_3["InputActivityRatio"]["FUEL"] != "COA"
    ]
    # Write edited CSVs
    output_folder_3 = "examples/otoole_csvs/otoole-full-electricity-edited-3"
    os.makedirs(output_folder_3, exist_ok=True)
    for df_name, df in csv_data_edited_3.items():
        df.to_csv(os.path.join(output_folder_3, f"{df_name}.csv"), index=False)

    return [output_folder_1, output_folder_2, output_folder_3]
