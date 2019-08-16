.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(PSAMPLE)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :

	rm -fr ./libpsample
	git clone https://github.com/Mellanox/libpsample.git
	cp -r debian libpsample

	pushd ./libpsample
	git checkout -b libpsample -f e48fad2

	# get the dpkg lock and install libmnl-dev
	while true; do
	if mkdir $(DEST)/dpkg_lock &> /dev/null; then
	{ sudo apt-get install -f -y libmnl-dev=1.0.4-2 && rm -d $(DEST)/dpkg_lock && break; } || { rm -d $(DEST)/dpkg_lock && exit 1 ; }
	fi
	done

	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $* $(DEST)/

