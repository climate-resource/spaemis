# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -pycharm
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import os

from spaemis.constants import TEST_DATA_DIR
from spaemis.inventory import load_inventory
from spaemis.scaling import RelativeChangeScaler

# %%
INPUT_DATA = os.path.join(TEST_DATA_DIR, "input4MIPs")


# %%
inventory = load_inventory("victoria", 2016)
inventory

# %%

scaler = RelativeChangeScaler(
    "OC-em-anthro", source_id="IAMC-MESSAGE-GLOBIOM-ssp245-1-1"
)
scaler(inventory=inventory, target_year=2060)

# %%
