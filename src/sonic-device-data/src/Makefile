.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

test:
	# Execute Broadcom config file test
	pushd ../tests/
	for f in `find ../../../device -name "*.config.bcm"`; do
		echo ./config_checker $$f
		./config_checker $$f
	done
	popd
