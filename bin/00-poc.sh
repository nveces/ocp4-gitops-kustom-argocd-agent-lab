#!/bin/bash
#
# ============================================================
# Based on the https://developers.redhat.com/blog/2025/10/06/using-argo-cd-agent-openshift-gitops
#              (Created by Gerald Nunn https://developers.redhat.com/author/gerald-nunn)
#
# See also: https://github.com/gitops-examples/openshift-gitops-agent
#           https://github.com/argoproj-labs/argocd-agent/
# ============================================================
# Description---: Start a Proof of Concept for Argo CD Agent with OpenShift GitOps
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