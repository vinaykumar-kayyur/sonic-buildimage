###########################################################################
##
## File:        ./Makefile.am
## Versions:    $Id: Makefile.am,v 1.0 2021/08/24 12:04:29 liuh@microsoft.com Exp $
## Created:     2021/08/24
##
###########################################################################

ACLOCAL_AMFLAGS = -I config
AUTOMAKE_OPTIONS = subdir-objects

bin_PROGRAMS = tacplus-probe
tacplus_probe_SOURCES = tacplus_probe.h tacplus_probe.cpp
tacplus_probe_CFLAGS = $(DBGFLAGS) $(AM_CFLAGS) $(CFLAGS_COMMON) -I $(top_srcdir)/libtac/include
tacplus_probe_CPPFLAGS = $(DBGFLAGS) $(AM_CPPFLAGS) $(CFLAGS_COMMON) -I $(top_srcdir)/libtac/include
tacplus_probe_LDFLAGS = -Wl,-z,now $(LDFLAGS) -lswsscommon


EXTRA_DIST = tacplus_probe.spec

MAINTAINERCLEANFILES = Makefile.in config.h.in configure aclocal.m4 \
                       config/config.guess  config/config.sub  config/depcomp \
                       config/install-sh config/ltmain.sh config/missing

pkgconfigdir = $(libdir)/pkgconfig

