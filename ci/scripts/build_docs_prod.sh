#!/bin/bash

set -eu

pulp-docs fetch --fetch-all --dest /tmp/fetchdir
pulp-docs build --path "pulp-docs@..:/tmp/fetchdir"
ls site || (echo "ERROR: something went wrong, 'site/' dir doesn't exist"; exit 1)
