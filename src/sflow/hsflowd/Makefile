.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(HSFLOWD)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -fr ./host-sflow
	git clone https://github.com/sflow/host-sflow

	pushd ./host-sflow
	git checkout -b sflow -f 5f171bb

        # Apply patch series
	stg init
	stg import -s ../patch/series

	make deb FEATURES="SONIC"
	mv $* $(DEST)/
	popd

