#!/bin/bash
# 
# This scripts gets the latest version code from a repository without
# needing to clone the whole repo.
#
# https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#get-the-latest-release

OWNER="pulp"
REPO="pulpcore"

gh api \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "/repos/$OWNER/$REPO/releases/latest" > response

set -x
tarball_url="$(cat response | jq '.tarball_url' | tr -d '"')"

mkdir -p outdir
wget -O output.tar "$tarball_url"
tar -xf output.tar --directory outdir
ls outdir
