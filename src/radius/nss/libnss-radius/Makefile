#######################################################################
#
# Copyright 2019 Broadcom. All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
#
#######################################################################

#
# Makefile for libnss-radius
#


# For now place the multiarch flag here
# Eventually this needs to be move to the debian packaging
#moduledir = $(prefix)/lib/x86_64-linux-gnu
moduledir = $(prefix)/lib/$(DEB_HOST_MULTIARCH)


all: libnss_radius.so.2 cache_radius rbash_restriction.sh

libnss_radius.so.2: nss_radius.c nss_radius_common.c
	$(CC) $(CFLAGS) $(LDFLAGS) -fPIC -Wall -shared -o libnss_radius.so.2 \
		-Wl,-soname,libnss_radius.so.2 nss_radius.c

cache_radius: cache_radius.c nss_radius_common.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o cache_radius cache_radius.c

clean:
	-rm -f libnss_radius.so.2 cache_radius
	-rm -f test_nss_radius test_cache_radius

install: libnss_radius.so.2 cache_radius rbash_restriction.sh
	install -m 0644 -D libnss_radius.so.2 $(DESTDIR)$(moduledir)/libnss_radius.so.2
	install -m 0755 -D cache_radius $(DESTDIR)$(prefix)/usr/sbin/cache_radius
	install -m 0755 -d $(DESTDIR)$(prefix)/etc/pam_radius_auth.d/
	install -m 0644 -D rbash_restriction.sh $(DESTDIR)$(prefix)/etc/profile.d/rbash_restriction.sh

distclean: clean

uninstall:
	-rm -f $(DESTDIR)$(moduledir)/libnss_radius.so.2
	-rm -f $(DESTDIR)$(prefix)/usr/sbin/cache_radius
	-rm -f $(DESTDIR)$(prefix)/etc/profile.d/rbash_restriction.sh

test: nss_radius.c test_nss_radius.c
	$(CC) $(CFLAGS) $(LDFLAGS) -g -o test_nss_radius test_nss_radius.c
	$(CC) $(CFLAGS) $(LDFLAGS) -g -DTEST_RADIUS_NSS -o test_cache_radius cache_radius.c
	

.PHONY: all install clean distclean uninstall test

