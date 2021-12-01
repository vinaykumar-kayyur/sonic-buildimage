#!/bin/bash
 
source ./build.cfg
 
#Helper functions start###
function checkErrors()
{
    X=`grep -i -c "${1}" "${2}"`
    if [ "${X}" != "0" ];then
       grep -i -n "${1}" "${2}"
    fi
}
 
function doSetup()
{
  CONFIGZTP="ENABLE_ZTP=${ENABLE_ZTP}"
  CONFIGSONIC="{$CONFIGZTP}"
}
 
function doMakeConfig()
{
  #Execute make configure once to configure ASIC
  #make configure PLATFORM=[ASIC_VENDOR]
  make configure PLATFORM=vs
}
 
# Build SONiC image
function doMake()
{
  LOGFILE="../logs/${BLDDIR}.log"
  echo "time make
SONIC_BUILD_JOBS=24 ${SONIC_OVERRIDE_BUILD_VARS}
target/sonic-vs.bin" > "${LOGFILE}"
  time make SONIC_BUILD_JOBS=24 ${SONIC_OVERRIDE_BUILD_VARS} target/sonic-vs.bin | tee "${LOGFILE}"
  checkErrors "fail" "${LOGFILE}"
  checkErrors "warning" "${LOGFILE}"
  checkErrors "error" "${LOGFILE}"
}
#Helper functions end###
 
cd "${BLDDIR}"
doSetup
doMakeConfig
doMake