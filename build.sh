#!/bin/bash
make init
#NOSTRETCH=y NOJESSIE=y NOBUSTER=y make configure PLATFORM=broadcom
NOJESSIE=y NOBULLSEYE=y make configure PLATFORM=vs
# NOSTRETCH=y NOJESSIE=y make ENABLE_SYNCD_RPC=y SAITHRIFT_V2=y target/docker-ptf-sai.gz
# NOSTRETCH=y NOJESSIE=y NOBUSTER=y ENABLE_SYNCD_RPC=y SAITHRIFT_V2=y make target/docker-syncd-brcm-rpcv2.gz
#NOSTRETCH=y NOJESSIE=y NOBUSTER=y ENABLE_SYNCD_RPC=y make target/docker-saiserver-brcm.gz
# NOSTRETCH=y NOJESSIE=y NOBUSTER=y SAITHRIFT_V2=y make target/docker-saiserverv2-brcm.gz
# cp target/debs/bullseye/python-saithriftv2_0.9.4_amd64.deb target/python-saithriftv2_0.9.4_amd64.deb
# NOSTRETCH=y NOJESSIE=y NOBUSTER=y ENABLE_SYNCD_RPC=y make target/docker-syncd-brcm-rpc.gz
NOJESSIE=y NOBULLSEYE=y SAITHRIFT_V2=y make target/docker-ptf-sai.gz
