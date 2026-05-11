#!/bin/bash

set -eu

COMPONENT="$1"

pulp-docs build --path "pulp-docs@..:${COMPONENT}@.." --draft
ls site || (echo "ERROR: something went wrong, 'site/' dir doesn't exist"; exit 1)
