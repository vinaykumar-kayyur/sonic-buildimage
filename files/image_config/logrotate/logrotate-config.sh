#!/bin/bash

# Reserve space for btmp and wtmp, auth.log and cron.log, as well as logs that
# should be disabled, just in case they get created and rotated
RESERVED_SPACE_KB=1024

# Number of rotated archive files to keep per log file
NUM_ARCHIVES_PER_LOG_FILE=7

# Number of files to rotate in each block within rsyslog.j2 template
NUM_LOG_FILES_SYSLOG=1
NUM_LOG_FILES_QUAGGA_TEAMD=3
NUM_LOG_FILES_SWSS=2

# Percentage of usable /var/log/ space to allocate to each block in template
# NOTE: These must sum to 100!
PERCENT_ALLOCATED_SYSLOG=75
PERCENT_ALLOCATED_QUAGGA_TEAMD=15
PERCENT_ALLOCATED_SWSS=10

VAR_LOG_SIZE_KB=$(df /var/log | sed -n 2p | awk '{print $2}')
USABLE_SPACE_KB=$((VAR_LOG_SIZE_KB - RESERVED_SPACE_KB))

SIZE_LIMIT_SYSLOG_FILES_KB=$((USABLE_SPACE_KB / (NUM_LOG_FILES_SYSLOG * (NUM_ARCHIVES_PER_LOG_FILE + 1)) / 100 * PERCENT_ALLOCATED_SYSLOG))
SIZE_LIMIT_QUAGGA_TEAMD_FILES_KB=$((USABLE_SPACE_KB / (NUM_LOG_FILES_QUAGGA_TEAMD * (NUM_ARCHIVES_PER_LOG_FILE + 1)) / 100 * PERCENT_ALLOCATED_QUAGGA_TEAMD))
SIZE_LIMIT_SWSS_FILES_KB=$((USABLE_SPACE_KB / (NUM_LOG_FILES_SWSS * (NUM_ARCHIVES_PER_LOG_FILE + 1)) / 100 * PERCENT_ALLOCATED_SWSS))

ADDITIONAL_DATA_JSON="{"
ADDITIONAL_DATA_JSON+="\"num_archive_files\":$NUM_ARCHIVES_PER_LOG_FILE,"
ADDITIONAL_DATA_JSON+="\"size_limit_syslog_kb\":$SIZE_LIMIT_SYSLOG_FILES_KB,"
ADDITIONAL_DATA_JSON+="\"size_limit_quagga_teamd_kb\":$SIZE_LIMIT_QUAGGA_TEAMD_FILES_KB,"
ADDITIONAL_DATA_JSON+="\"size_limit_swss_kb\":$SIZE_LIMIT_SWSS_FILES_KB"
ADDITIONAL_DATA_JSON+="}"

sonic-cfggen -a "$ADDITIONAL_DATA_JSON" -t /usr/share/sonic/templates/logrotate.d/rsyslog.j2 > /etc/logrotate.d/rsyslog
