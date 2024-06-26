#!/bin/bash

echo "Fetching changes..."
git fetch

if [[ -n "$(git log origin/main ^main)" ]]; then
  echo "Changes detected, updating..."
  git rebase origin/main
  source "${PWD}"/.venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart uon-ce
  echo "Done."
else
  echo "No changes detected."
fi
