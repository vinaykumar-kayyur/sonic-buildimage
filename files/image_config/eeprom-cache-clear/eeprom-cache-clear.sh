#! /bin/bash
## Clear EEPROM cache

CACHE_ROOT="/var/cache/sonic/decode-syseeprom"
CACHE_FILE="syseeprom_cache"

mkdir -p ${CACHE_ROOT}
rm -f ${CACHE_ROOT}/${CACHE_FILE}
