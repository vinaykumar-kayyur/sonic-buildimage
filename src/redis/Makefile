SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

REDIS_VERSION = 3.2.13
REDIS_VERSION_FULL = $(REDIS_VERSION)-1~bpo8+1

MAIN_TARGET = redis-server_$(REDIS_VERSION_FULL)_amd64.deb
DERIVED_TARGETS = redis-tools_$(REDIS_VERSION_FULL)_amd64.deb \
		  redis-sentinel_$(REDIS_VERSION_FULL)_amd64.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	wget -O redis_$(REDIS_VERSION).orig.tar.gz -N "https://nam06.safelinks.protection.outlook.com/?url=https%3A%2F%2Fsonicstorage.blob.core.windows.net%2Fpackages%2Fredis%2Fredis_3.2.13.orig.tar.gz%3Fsv%3D2015-04-05%26sr%3Db%26sig%3DDE%252F3Gb3%252BabCrtUJqCPyfU1OTJCANGYkBrdEKi%252FJYMQQ%253D%26se%3D2033-05-19T16%253A43%253A53Z%26sp%3Dr&data=02%7C01%7CRenuka.Manavalan%40microsoft.com%7C0b8c3585f5614ad0ae3808d7360e2296%7C72f988bf86f141af91ab2d7cd011db47%7C1%7C0%7C637037306647661880&sdata=aq40gNNBj05DufpIVDIV9OTz2lUGmM%2FMpoBaWBnMSFc%3D&reserved=0"
	wget -O redis_$(REDIS_VERSION_FULL).dsc -N "https://nam06.safelinks.protection.outlook.com/?url=https:%2F%2Fsonicstorage.blob.core.windows.net%2Fpackages%2Fredis%2Fredis_3.2.13-1~bpo8%2B1.dsc%3Fsv%3D2015-04-05%26sr%3Db%26sig%3DmQ502FHWRiOFb9cjEUcK0r1gXAc3bBv0fmVEWtroy5c%253D%26se%3D2033-05-19T16%253A43%253A29Z%26sp%3Dr&data=02%7C01%7CRenuka.Manavalan%40microsoft.com%7C0b8c3585f5614ad0ae3808d7360e2296%7C72f988bf86f141af91ab2d7cd011db47%7C1%7C0%7C637037306647651889&sdata=bFx8z%2FglIZ4j%2F4H8NzHeoju%2BbVK0BoGfkfX%2FVtTbykk%3D&reserved=0"
	wget -O redis_$(REDIS_VERSION_FULL).debian.tar.xz -N "https://nam06.safelinks.protection.outlook.com/?url=https:%2F%2Fsonicstorage.blob.core.windows.net%2Fpackages%2Fredis%2Fredis_3.2.13-1~bpo8%2B1.debian.tar.xz%3Fsv%3D2015-04-05%26sr%3Db%26sig%3DiboHl5%252BV6zUcS5%252B8CaNnE9A0qLa7H%252BU8P1H0eofWjig%253D%26se%3D2033-05-19T16%253A43%253A00Z%26sp%3Dr&data=02%7C01%7CRenuka.Manavalan%40microsoft.com%7C0b8c3585f5614ad0ae3808d7360e2296%7C72f988bf86f141af91ab2d7cd011db47%7C1%7C0%7C637037306647651889&sdata=EPk1mIb67YKKLsMLFBLeRQxLC981mn0RE0SHh2weVSA%3D&reserved=0"
	dpkg-source -x redis_$(REDIS_VERSION_FULL).dsc

	pushd redis-$(REDIS_VERSION)
	DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS)
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
