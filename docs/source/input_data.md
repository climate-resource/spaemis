# Input data

A number of different input datasets are required to run `spaemis`. A basic set of
input data have been included in this repository and are described below. `spaemis`
was designed to be flexible and able to be extended so additional proxies can be
added depending on the use case.

Some input4MIPs data is required to be downloaded before running.

## Emissions inventories

This project bundles two emissions inventories with the repository, a Victorian
inventory for 2016 developed by the Victorian EPA, and an Australian-wide inventory
that uses EDGAR data. These inventories are included in the repository in `data/raw/inventories`.

Each inventory has a different format, but {py:mod}`spaemis.inventory` for more information
about the reading/processing of these inventories. For testing purposes, these
inventories have been downsampled to much coarser resolutions and included in
`tests/test-data/inventory`

The location of the emissions inventory files can be specified using the
`SPAEMIS_INVENTORY_DIRECTORY` environment variable.

### Victorian Inventory

The licensing for this inventory is currently being finalised so while the
data files for this invetory have been included in the repository, they are
contained in an GPG encrypted file. Contact `@lewisjarednz` if you require
access.


### Australian Inventory

This inventory was generated using EDGAR v6.1 data via the notebook located at
`notebooks/exploratory/300_build_aus_inventory.py`.

The raw EDGAR data can be downloaded using the script located at `scripts/download_edgar.py`.

## input4MIPs

Input4MIPs emissions datasets can be used in many of the scaling routines. A database of
available input datasets is maintained and the scaling uses the `source_id` and
`variable_id` are used to uniquely identify datasets.

It is recommended to download the following `variable_id`s from [ESGF's input4MIPs archive](https://esgf-node.llnl.gov/search/input4mips/):

* BC-em-anthro
* CH4-em-anthro
* CO-em-anthro
* CO2-em-anthro
* NH3-em-anthro
* NMVOC-em-anthro
* NOx-em-anthro
* OC-em-anthro
* SO2-em-anthro


The `source_id`s are of the form: `IAMC-{IAM}-{ssp}-1-1`. For example: `IAMC-IMAGE-ssp126-1-1`.

The location of the input4MIPs files can be specified using the
`SPAEMIS_INPUT_PATHS` environment variable. Multiple search locations
can be specified using a comma-separated list.

## Proxies

Arbitrary proxy fields can also be used during scaling. A population proxy derived
from SEDACs has been included in the repository at `data/processed/proxies`.
See `scripts/extract_sedacs.py` for the script used to generate this proxy.

The location of the proxy files can be specified using the
`SPAEMIS_PROXY_DIRECTORY` environment variable.


## Point Sources

A bulk amount of emissions can be spread across a number of point sources. There are two
predefined point source definitions are provided in `data/raw/configuration/point_sources`:

* `federal_locations` - A list of potential H2 hubs specified by the Australian
  Federal Government (TODO: cite)
* `hysupply_locations` - A list of potential H2 hubs specified by the hysupply
  project, an  Australia-Germany collaboration that identified 41 potential sites (TODO: cite)

Each point source file is a CSV with at least the columns: `id, lat, lon`. Each row
represents a single location.

The location of the point source definition files can be specified using the
`SPAEMIS_POINT_SOURCE_DIRECTORY` environment variable.
