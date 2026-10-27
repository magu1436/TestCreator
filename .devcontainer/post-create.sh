#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Named volumes may be owned by root on their first use.
sudo chown "$(id -u):$(id -g)" node_modules
bash scripts/setup-dev.sh
