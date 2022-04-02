###########################################################################
##
## File:        ./Makefile.am
## Versions:    $Id: Makefile.am,v 1.0 2022/04/02 12:04:29 liuh@microsoft.com Exp $
## Created:     2022/04/02
##
###########################################################################

ACLOCAL_AMFLAGS = -I config
AUTOMAKE_OPTIONS = subdir-objects

bin_PROGRAMS = sonic-cli
sonic_cli_SOURCES = sonic-cli.h \
                    sonic-cli.cpp
sonic_cli_CPPFLAGS = $(AM_CPPFLAGS)
sonic_cli_LDFLAGS = -lswsscommon

EXTRA_DIST = sonic-cli.spec

MAINTAINERCLEANFILES = Makefile.in config.h.in configure aclocal.m4 \
                       config/config.guess  config/config.sub  config/depcomp \
                       config/install-sh config/ltmain.sh config/missing

pkgconfigdir = $(libdir)/pkgconfig
