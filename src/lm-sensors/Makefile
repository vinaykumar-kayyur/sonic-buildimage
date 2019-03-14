SHELL = /bin/bash
.ONESHELL:
	.SHELLFLAGS += -e


MAIN_TARGET = $(LM_SENSORS)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf lm-sensors-$(LM_SENSORS_VERSION)
	dget -u http://deb.debian.org/debian/pool/main/l/lm-sensors/lm-sensors_3.4.0-4.dsc
	sed -i "/Binary: lm-sensors, libsensors4, libsensors4-dev, fancontrol/c\Binary: lm-sensors, libsensors4, libsensors4-dev, fancontrol, sensord/g" lm-sensors_3.4.0-4.dsc
	pushd lm-sensors-$(LM_SENSORS_VERSION)
	DEB_BUILD_OPTIONS=nocheck PROG_EXTRA=sensord dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $* $(DEST)/
