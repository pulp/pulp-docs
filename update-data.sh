#!/bin/bash
set -eu -o pipefail

# generate data
python -m pulp_docs.openapi data/openapi_json

# commit changes
BRANCH=$(git branch --show-current)
if ! [[ "${BRANCH}" = "docs-data" ]]
then
  echo ERROR: This is not a data-branch!
  exit 1
fi

git add data/*
git commit -m "Update data files: $(date --iso-8601=minutes)"
git push origin docs-data
