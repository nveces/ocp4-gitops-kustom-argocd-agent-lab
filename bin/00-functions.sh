#!/bin/bash
#
# ============================================================
#
#
# Created-------: 20200324
# ============================================================
# Description--: Common Functions
#
# ============================================================
#
# ============================================================
# Pre Steps---:
# chmod 774 *.sh
# ============================================================
#
#
#### LOG VERBOSITY
# 0 - NONE--: No registra ningun mensaje
# 1 - ERROR-: Registra solo mensajes de error
# 2 - WARN--: Registra mensajes de alerta
# 3 - INFO--: Registra solo mensajes de error y informativos
# 4 - DEBUG-: Registra mensajes de error, informativos y de debug
#
# EOH

# Default 3
LOG_LEVEL=3
SCREEN_ONLY=""

# colors
# Black       0;30     Dark Gray     1;30
# Blue        0;34     Light Blue    1;34
# Green       0;32     Light Green   1;32
# Cyan        0;36     Light Cyan    1;36
# Red         0;31     Light Red     1;31
# Purple      0;35     Light Purple  1;35
# Brown       0;33     Yellow        1;33
# Light Gray  0;37     White         1;37

black='\e[0;30m'
blue='\e[0;34m'
green='\e[0;32m'
cyan='\e[0;36m'
red='\e[0;31m'
brown='\e[0;33m'
lgray='\e[0;37m'
#
reset='\e[0m'
bold='\e[1m'
#
col_dbg='\e[0;34m'
col_msg='\e[0;32m'
col_warn='\e[0;33m'
col_err='\e[0;31m'


#############################
# Utility functions for OCP #
#############################
function check_login(){

  WHOAMI=$(oc whoami 2> /dev/null)
  RESULT=$?
  if [ ${RESULT} -ne 0 ]; then
    err "You aren't logged"
    exit 1
  fi
}

function check_login_namespace(){
    local project_target=$1
    check_login
    if has_namespace "${project_target}"; then
      msg "The '${project_target}' namespace exists in the OCP cluster"
    else
      err "The '${project_target}' namespace doesn't exist or you cannot get the namespace '${project_target}'"
      exit 1
    fi
}

function has_namespace() {
  if oc get namespace "$1" &> /dev/null; then
    true
  else
    false
  fi
}

function check_login_project(){
  local project_target=$1

  WHOAMI=$(oc whoami 2> /dev/null)
  RESULT=$?
  if [ ${RESULT} -ne 0 ]; then
    err "You aren't login"
    exit 1
  else
    PROJECT=$(oc project -q)
    msg "I'm '${WHOAMI}' and I'm in the '${PROJECT}' project"
    if [ "${PROJECT}" != "${project_target}" ]; then
      err "Your aren't in the '${project_target}' project. Your are using '${PROJECT}'"
      exit 1
    fi
  fi
}

function check_object_in_namespace(){
  local objectytpe=$1
  local objectname=$2
  local projectTarget=$3

  OBJ=$(oc get $1/$2  -n ${projectTarget} --output=go-template={{.metadata.name}} --no-headers 2>/dev/null)
  if [ -z ${OBJ} ]; then
    err "The '$2' object of '$1' type doesn't exists and it's a mandatory object for the installation. Please create it!!"
  else
    msg "The '$2' object of '$1' type exists and the '${projectTarget}' namespace"
  fi
}


#################################
# Utility functions for Logging #
#################################
LINE_PADDING=''
CHAR_CAPTION="."
LINE_PAD_LENGTH=30
for ((i=0; i<$LINE_PAD_LENGTH; i++)); do
    LINE_PADDING+=$CHAR_CAPTION
done
LINE_PADDING+=":"


function date_logf() {
    #date "+%a %d %b %Y %T"
    date "+[%F %T]"
}

function date_gc() {
    date "+%F"
}

function date_dump() {
    date "+%F_%H-%M-%S"
}

function _log(){
    if [ $LOG_LEVEL -gt $1 ]; then
        printf "%b%s %s: ${bold}%s${reset} %b%s${reset}\n" $5 "$(date_logf)" "$2" "$4"  $5 "$3"
    fi
}

function err() {
    _log 0 "[ERROR]" "$1" "[KO]" ${col_err}
}

function warn() {
    _log 1 "[WARN]" "$1" "[OK?]" ${col_warn}
}

function msg() {
    _log 2 "[INFO]" "$1" "[OK]" ${col_msg}
}

function dbg() {
    _log 3 "[DEBUG]" "$1" "[--]" ${col_dbg}
}


###############################
# Utility functions for Usage #
###############################
function usage_info(){
  echo "Usage: $0 [-n | --namespace] <namespace>"
  echo ""
  echo "Parameters:"
  echo "  -n | --namespace  Project/Namespace"
  exit 1
}

function usage_info_env(){
  echo "Usage: $0 [environment]"
  echo ""
  echo "Possible values for environment:"
  echo "  -l | --lab   Laboratorio Environment"
  echo "  -d | --dev   Development Environment"
  echo "  -t | --tst   Test Environment"
  echo "  -p | --pro   Production Environment"
  exit 1
}

#
# EOF
