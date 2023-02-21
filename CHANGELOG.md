
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Types of changes**
* `Added` for new features
* `Changed` for changes in existing functionality
* `Deprecated` for soon-to-be removed features
* `Removed` for now removed features
* `Fixed` for any bug fixes
* `Security` in case of vulnerabilities

## [Unreleased]

### Added

- Add timeseries data to scaling calculation and create a new `ProxyScaler` scaler which uses a timeseries and a spatial pattern to disaggregate total emissions [#12](https://github.com/climate-resource/spaemis/pull/12)
- Add `ssp119`, `ssp126` and `ssp245` scenario configurations [#10](https://github.com/climate-resource/spaemis/pull/10)
- Add `default_scaler` to the configuration for the scaler to be used if no specific scaler configuration is provided [#9](https://github.com/climate-resource/spaemis/pull/9)
- Move test configuration to `test-data` directory  [#8](https://github.com/climate-resource/spaemis/pull/8)
- Add functionality to write out a xarray dataset as a set of CSVs that are formatted the same as the input emissions inventory data  [#7](https://github.com/climate-resource/spaemis/pull/7)
- Add relative_change scaler and reading of Input4MIPs data [#3](https://github.com/climate-resource/spaemis/pull/3)
- Added CLI command `project` and a framework for scalers [#2](https://github.com/climate-resource/spaemis/pull/2)
- Initial commit and repository setup
