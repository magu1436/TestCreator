#!/usr/bin/env bash
set -euo pipefail

if [[ "${TESTCREATOR_DEVCONTAINER:-}" != "1" ]]; then
    echo "TypeScript watch starts automatically only inside the DevContainer."
    exit 0
fi

cd /workspaces/TestCreator
# Share the lock across VS Code windows and release it when the task stops.
exec flock --nonblock --conflict-exit-code 0 /tmp/testcreator-watch.lock npm run watch
