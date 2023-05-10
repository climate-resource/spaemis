"""
Constants
"""
import os

OUTPUT_VERSION = "v20230421_1"

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_DATA_DIR = os.path.join(ROOT_DIR, "tests", "test-data")

DATA_DIR = os.path.join(ROOT_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(
    DATA_DIR,
    "processed",
)

RUNS_DIR = os.path.join(DATA_DIR, "runs", OUTPUT_VERSION)

# Define the root variables that we support in this tool
# Any variables should be renamed to these names

#     "Emissions|CO2",
#     "Emissions|VOC",
#     "Emissions|NOx",
#     "Emissions|Sulfur",
#     "Emissions|PM10",
