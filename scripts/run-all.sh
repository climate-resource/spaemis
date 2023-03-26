#!/usr/bin/env bash
# Runs the notebooks via the cli
# Usage: bash scripts/run-all.sh

set -e


CONFIGS="data/raw/configuration/scenarios/*.yaml"

echo "Found the following configurations:"
printf "'%s'\n" "$CONFIGS"
echo

for config in $CONFIGS; do
  echo "Processing $config"
  spaemis run --force -c $config
  echo
  echo
done
