SHELL = /bin/bash

MAIN_TARGET = redis-server_3.0.7-2_amd64.deb
DERIVED_TARGETS = redis-tools_3.0.7-2_amd64.deb redis-sentinel_3.0.7-2_amd64.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	wget -O redis_3.0.7-2.dsc 'https://sonicstorage.blob.core.windows.net/packages/redis_3.0.7-2.dsc?sv=2015-04-05&sr=b&sig=evQtsWTIUFlgWbzLLifS1lDgop%2BzlqIP8ehZl3p%2FCKI%3D&se=2026-07-24T01%3A48%3A19Z&sp=r'
	wget -O redis_3.0.7.orig.tar.gz 'https://sonicstorage.blob.core.windows.net/packages/redis_3.0.7.orig.tar.gz?sv=2015-04-05&sr=b&sig=0ht16%2Fi8%2FPZQHp1PrDPYW0iRwcLfUPw1JpKUapizu8o%3D&se=2026-07-24T01%3A48%3A49Z&sp=r'
	wget -O redis_3.0.7-2.debian.tar.xz 'https://sonicstorage.blob.core.windows.net/packages/redis_3.0.7-2.debian.tar.xz?sv=2015-04-05&sr=b&sig=4a33ECTvURfNUEDkS436ZlSsIpLIC9QdJrBBRIoWpW0%3D&se=2026-07-24T01%3A49%3A22Z&sp=r'
	dpkg-source -x redis_3.0.7-2.dsc
	pushd redis-3.0.7; fakeroot debian/rules binary; popd
	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
