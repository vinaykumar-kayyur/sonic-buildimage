#!/bin/bash
#########################################################################
## This script is to automate Orignaization specific extensions 	#
## such as Configuration & Scripts for features like AAA, ZTP, etc.	#
## to include in ONIE installer image					#
##									#
## USAGE:								#
##   ./organization_extensions.sh FILESYSTEM_ROOT HOSTNAME		#
## PARAMETERS:								#
##   FILESYSTEM_ROOT							#
##          The location of the root file system			#
##   HOSTNAME								#
##          The hostname of the target system				#
#########################################################################

## Default Root Filesystem
FILESYSTEM_ROOT=$1
[ -n "$FILESYSTEM_ROOT" ] || {
    echo "Error: no or empty FILESYSTEM_ROOT argument"
    exit 1
}

## Default Hostname
HOSTNAME=$2
[ -n "$HOSTNAME" ] || {
    echo "Error: no or empty HOSTNAME argument"
    exit 1
}

echo "##### SONIC Organization Extensions #####"
## Place your Organization specific code / scipts here ... 


echo "##### SONIC Organization Extensions - Done #####"

