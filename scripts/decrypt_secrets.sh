#!/bin/sh
# Files encrypted using `gpg --symmetric --cipher-algo AES256 my_file`

# --batch to prevent interactive command
# --yes to assume "yes" for questions
gpg --quiet --batch --yes --decrypt --passphrase="$LARGE_SECRET_PASSPHRASE" \
  --output data/raw/inventories/victoria_2016.zip \
  data/raw/inventories/victoria_2016.zip.gpg

unzip -d data/raw/inventories data/raw/inventories/victoria_2016.zip

ls -al data/raw/inventories