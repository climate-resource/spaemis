#!/usr/bin/env bash
# Runs the notebooks via the cli
# Usage: bash scripts/run-all.sh

set -e


CONFIGS="data/raw/configuration/scenarios/*.yaml"

echo "Found the following configurations:"
printf "'%s'\n" "$CONFIGS"
echo

#for config in $CONFIGS; do
#  echo "Processing $config"
#  spaemis run --force -c $config
#  echo
#  echo
#done

#spaemis run --force -c data/raw/configuration/scenarios/ssp119_australia.yaml
spaemis run --force -c data/raw/configuration/scenarios/ssp226_australia.yaml
spaemis run --force -c data/raw/configuration/scenarios/ssp245_australia.yaml
#spaemis run --force -c data/raw/configuration/scenarios/ssp119_victoria.yaml
spaemis run --force -c data/raw/configuration/scenarios/ssp226_victoria.yaml
spaemis run --force -c data/raw/configuration/scenarios/ssp245_victoria.yaml
