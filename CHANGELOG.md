# Changelog

## v0.2.3 (2023-05-29)

### Feat

- Specify the point source directory using an environment variable (#31)

## v0.2.2 (2023-05-26)

### Feat

- Allow the inventory directory to be specified using the SPAEMIS_INVENTORY_DIRECTORY environment variable (#30)

## v0.2.1 (2023-05-22)

### Feat

- **proxies**: Allow the proxy directory to be specified using the SPAEMIS_PROXY_DIRECTORY environment variable

## v0.2.0 (2023-05-22)

## v0.2.0a2 (2023-05-22)

## [v0.1.0]

### Added

- Add PointSourceScaler  [#24](https://github.com/climate-resource/spaemis/pull/24)
- Figure generation for report  [#23](https://github.com/climate-resource/spaemis/pull/23)
- Add complete set of H2 scalers [#21](https://github.com/climate-resource/spaemis/pull/21)
- Update point source configuration [#19](https://github.com/climate-resource/spaemis/pull/19)
- Add command for generating point source configuration [#18](https://github.com/climate-resource/spaemis/pull/18)
- Add Australian gridding configuration [#17](https://github.com/climate-resource/spaemis/pull/17)
- Add script for downloading EDGARv6.1 data [#16](https://github.com/climate-resource/spaemis/pull/16)
- Refactor to write results as notebooks in `data/runs/{OUTPUT_VERSION}` [#15](https://github.com/climate-resource/spaemis/pull/15)
- Allow multiple source files containing scaler information to be read [#14](https://github.com/climate-resource/spaemis/pull/14)
- Add timeseries data to scaling calculation and create a new `ProxyScaler` scaler which uses a timeseries and a spatial pattern to disaggregate total emissions [#12](https://github.com/climate-resource/spaemis/pull/12)
- Add `ssp119`, `ssp126` and `ssp245` scenario configurations [#10](https://github.com/climate-resource/spaemis/pull/10)
- Add `default_scaler` to the configuration for the scaler to be used if no specific scaler configuration is provided [#9](https://github.com/climate-resource/spaemis/pull/9)
- Move test configuration to `test-data` directory  [#8](https://github.com/climate-resource/spaemis/pull/8)
- Add functionality to write out a xarray dataset as a set of CSVs that are formatted the same as the input emissions inventory data  [#7](https://github.com/climate-resource/spaemis/pull/7)
- Add relative_change scaler and reading of Input4MIPs data [#3](https://github.com/climate-resource/spaemis/pull/3)
- Added CLI command `project` and a framework for scalers [#2](https://github.com/climate-resource/spaemis/pull/2)
- Initial commit and repository setup


### Changed

- Renaming the ProxyScaler to TimeseriesScaler [#23](https://github.com/climate-resource/spaemis/pull/23)
