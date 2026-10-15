#!/bin/sh
set -eu
: "${MOTIONTALK_CHROME:?DraftCut must resolve the local Chrome executable first}"
exec /usr/bin/arch -arm64 "$MOTIONTALK_CHROME" "$@"
