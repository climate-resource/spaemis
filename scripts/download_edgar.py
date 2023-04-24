"""
Download script for EDGAR v6.1.

Data saved to data/raw/EDGARv6.1. Total disk size=~4GB
"""

import io
import itertools
import logging
import os
import zipfile

import joblib
import requests

from spaemis.constants import RAW_DATA_DIR

logger = logging.getLogger("download_edgar")
logging.basicConfig(level=logging.INFO)


# AGS - Agricultural soils: 4C+4D1+4D2+4D4 / 3C2+3C3+3C4+3C7
# AWB - Agricultural waste burning: 4F / 3C1b
# CHE - Chemical processes: 2B / 2B
# ENE - Power industry: 1A1a / 1A1a
# ENF - Enteric fermentation: 4A / 3A1
# FFF - Fossil Fuel Fires: 7A / 5B
# IDE - Indirect emissions from NOx and NH3: 7B+7C / 5A
# IND - Combustion for manufacturing: 1A2 / 1A2
# IRO - Iron and steel production: 2C1a+2C1c+2C1d+2C1e+2C1f+2C2 / 2C1+2C2
# NFE - Non-ferrous metals production: 2C3+2C4+2C5 / 2C3+2C4+2C5+2C6+2C7
# MNM - Manure management: 4B / 3A2
# N2O - Indirect N2O emissions from agriculture: 4D3 / 3C5+3C6
# PRO_COAL - Fuel exploitation COAL: 1B1a / 1B1a
# PRO_GAS - Fuel exploitation GAS: 1B2c / 1B2bi+1B2bii
# PRO_OIL - Fuel exploitation OIL: 1B2a1+1B2a2+1B2a3+1B2a4 / 1B2aiii2+1B2aiii3
# PRU_SOL - Solvents and products use: 3 / 2D3+2E+2F+2G
# RCO - Energy for buildings: 1A4 / 1A4+1A5
# REF_TRF - Oil refineries and Transformation industry: 1A1b+1A1c+1A5b1+1B1b+1B2a5+1B2a6+1B2b5+2C1b / 1A1b+1A1ci+1A1cii+1A5biii+1B1b+1B2aiii6+1B2biii3+1B1c # noqa
# SWD_INC - Solid waste incineration: 6C+6Dhaz / 4C
# SWD_LDF - Solid waste landfills: 6A+6Dcom / 4A+4B
# TNR_Aviation_CDS - Aviation climbing&descent: 1A3a_CDS / 1A3a_CDS
# TNR_Aviation_CRS - Aviation cruise: 1A3a_CRS / 1A3a_CRS
# TNR_Aviation_LTO - Aviation landing&takeoff: 1A3a_LTO / 1A3a_LTO
# TNR_Other - Railways, pipelines, off-road transport: 1A3c+1A3e / 1A3c+1A3e
# TNR_Ship - Shipping: 1A3d+1C2 / 1A3d
# TRO - Road transportation: 1A3b / 1A3b
# WWT - Waste water handling: 6B / 4D
SECTORS = (
    "AGS",
    "AWB",
    "CHE",
    "ENE",
    "ENF",
    "FOO_PAP",
    "FFF",
    "IDE",
    "IND",
    "IRO",
    "MNM",
    "N2O",
    "NEU",
    "NFE",
    "NMM",
    "PRO",
    # "PRO_COAL",
    # "PRO_GAS",
    # "PRO_OIL",
    "PRU_SOL",
    "RCO",
    "REF_TRF",
    "SWD_INC",
    "SWD_LDF",
    "TNR_Aviation_CDS",
    "TNR_Aviation_CRS",
    "TNR_Aviation_LTO",
    "TNR_Aviation_SPS",
    "TNR_Other",
    "TNR_Ship",
    "TRO_RES",
    "TRO_noRES",
    "WWT",
    "TOTALS",
)

SPECIES = ("BC", "CO", "NH3", "NMVOC", "NOx", "OC", "PM2.5", "PM10", "SO2")
YEAR = 2016
EDGAR_URL = "http://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP"


def download_file(gas: str, sector: str, year: int) -> None:
    exp_filename = f"EDGARv6.1_{gas}_{year}_{sector}.0.1x0.1.nc"
    out_dir = os.path.join(RAW_DATA_DIR, "EDGARv6.1", gas, sector)

    if os.path.exists(os.path.join(out_dir, exp_filename)):
        logger.info(f"{exp_filename} already downloaded")
        return

    resp = requests.get(
        os.path.join(
            EDGAR_URL, gas, sector, f"EDGARv6.1_{gas}_{year}_{sector}.0.1x0.1.zip"
        )
    )

    if resp.status_code == 404:
        return

    resp.raise_for_status()

    data = io.BytesIO(resp.content)
    zf = zipfile.ZipFile(data)

    os.makedirs(out_dir, exist_ok=True)
    zf.extract(exp_filename, os.path.join(out_dir))
    logger.info(f"{exp_filename} completed")


options = itertools.product(SPECIES, SECTORS, [YEAR])
download_file(SPECIES[0], SECTORS[1], YEAR)

joblib.Parallel(n_jobs=20)(joblib.delayed(download_file)(*opts) for opts in options)
