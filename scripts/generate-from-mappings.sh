#!/usr/bin/env bash
# Generate sector definition files from mapping yaml files
# Should be rerun after changing the yaml files

mappings='australia victoria'

scenario_sources='ssp119,IAMC-IMAGE-ssp119-1-1 ssp126,IAMC-IMAGE-ssp126-1-1 ssp245,IAMC-MESSAGE-GLOBIOM-ssp245-1-1'

OLDIFS=$IFS

for region in $mappings
do
  for scenario_info in $scenario_sources
  do
    IFS=','
    set -- $scenario_info
    echo $1 and $2

    spaemis generate --mappings data/raw/configuration/mappings/${region}_mappings.yaml --scaler-source $2 >| data/raw/configuration/scenarios/$1_${region}_scalers.csv
    IFS=$OLDIFS
  done
done
