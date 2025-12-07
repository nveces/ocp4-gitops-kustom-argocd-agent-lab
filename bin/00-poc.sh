#!/bin/bash
#
# ============================================================
#
#
# ============================================================
# Description---:
#
#
# ============================================================
#
# chmod 774 *.sh
#
#
# EOH

set -euo pipefail
#set -uo pipefail

# Step 1: Set current DIR and default variables:
V_ADMIN_DIR=$(dirname $0)
source ${V_ADMIN_DIR}/00-functions.sh

python ${V_ADMIN_DIR}/../tools/10-start-poc.py


msg "End of script."
exit 0
# EOF