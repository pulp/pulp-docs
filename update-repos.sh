#!/bin/bash
# Update repositories (stage all and commit)
REPOSITORIES=(new_repo1 new_repo2 new_repo3)
for repo in ${REPOSITORIES[@]}
do
  old_version=$(cat ../$repo/VERSION)
  new_version=$(python -c "print($old_version + 1)")
  echo $new_version > ../$repo/VERSION
  git -C "../$repo" add .
  git -C "../$repo" commit -m 'commit $new_version'
  echo "Done"
done
