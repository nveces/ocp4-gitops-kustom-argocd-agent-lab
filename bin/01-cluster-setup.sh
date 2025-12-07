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

#set -euo pipefail
set -o pipefail

# Step 1: Set current DIR and default variables:
V_ADMIN_DIR=$(dirname $0)
source ${V_ADMIN_DIR}/00-functions.sh

# Inicializar variables
FUNCTION_TO_RUN=""
NEW_ARGS=()

# -----------------------------------------------
# 2. router logic
# -----------------------------------------------
# Step 2 - Parser Input Parameters
while [ $# -gt 0 ]; do
    case $1 in
        -f | --func )     shift
                          FUNCTION_TO_RUN="$1"
                          ;;
        * )               NEW_ARGS+=("$1")
                          ;;
    esac
    shift
done


# Función para manejar errores de script
handle_error() {
    local retval=$?
    if [ $retval -ne 0 ]; then
        echo "🚨 ERROR: El script falló en la función $1. retval: ${retval}" #>&2
        exit $retval
    fi
}

# -----------------------------------------------
# 1. FUNCIONES A LLAMAR
# -----------------------------------------------

function switch_context_principal() {
    # msg "Parameters: $@"
    oc project argocd
    # Reset any existing 'principal' context:
    oc config get-contexts | grep -w "principal" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        msg "Context 'principal' exists . Deleting..."
        oc config delete-context principal
    fi
    oc config rename-context $(oc whoami -c) principal
    #oc config rename-context argocd/<cluster-api>/<user> principal
}

function switch_context_managed_cluster(){
    oc project argocd
    # Reset any existing 'managed-cluster' context:
    context_name="managed-cluster"
    oc config get-contexts | grep -w "${context_name}" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        msg "Context 'managed-cluster' exists . Deleting..."
        oc config delete-context ${context_name}
    fi
    oc config rename-context $(oc whoami -c) ${context_name}
    #oc config rename-context argocd/<cluster-api>/<user> ${context_name}
}

function create_issue_principal() {
    export SUBDOMAIN=$(oc get dns cluster -o jsonpath='{.spec.baseDomain}')
    argocd-agentctl pki issue principal --dns argocd-agent-principal-argocd.apps.$SUBDOMAIN --principal-context principal --principal-namespace argocd
}

function create_secret_argocd_redis(){
    oc create secret generic argocd-redis -n argocd --from-literal=auth="$(oc get secret argocd-redis-initial-password -n argocd -o jsonpath='{.data.admin\.password}' | base64 -d)"
}

function create_agent_on_principal() {
    argocd-agentctl agent create managed-cluster \
    --principal-context principal \
    --principal-namespace argocd \
    --resource-proxy-server argocd-agent-resource-proxy.argocd.svc.cluster.local:9090 \
    --resource-proxy-username foo \
    --resource-proxy-password bar
}

function deploy_agent_on_remote_cluster() {
    kustomize build managed-cluster/agent/base | envsubst | oc apply -f -
}

# -----------------------------------------------
# 3. Execution
# -----------------------------------------------

if [ -z "${FUNCTION_TO_RUN}" ]; then
    err "🚨 ERROR: The '-f' parameter is missing." #>&2
    exit 1
fi

# Check if the function exists
if ! declare -f "${FUNCTION_TO_RUN}" > /dev/null; then
    err "🚨 ERROR: The '$FUNCTION_TO_RUN' function is not defined in this script" #>&2
    exit 1
fi

msg "🎉 --- Running: ${FUNCTION_TO_RUN} ..."
# Call to function and pass the rest of the arguments
"${FUNCTION_TO_RUN}" "${NEW_ARGS[@]}"

# Handle Possible Error
handle_error "$FUNCTION_TO_RUN"

msg "✅ --- The ${FUNCTION_TO_RUN} function completed ---"


exit 0
#
# EOF