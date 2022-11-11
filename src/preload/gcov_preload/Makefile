#gcov Makefile

MKDIR := mkdir
MV := mv
#OBJ=gcov_preload.o
LIBNAME=libgcovpreload

# Fallback to gcc when $CC is not in $PATH.
CC:=$(shell sh -c 'type $${CC%% *} >/dev/null 2>/dev/null && echo $(CC) || echo gcc')
CXX:=$(shell sh -c 'type $${CXX%% *} >/dev/null 2>/dev/null && echo $(CXX) || echo g++')

DYLIBSUFFIX=so
DYLIBNAME=$(LIBNAME).$(DYLIBSUFFIX)
DYLIB_MAKE_CMD=$(CC) -shared -fpic gcov_preload.c -o ${DYLIBNAME}

$(DYLIBNAME):
	$(DYLIB_MAKE_CMD)

# Other Targets
install:
	$(MKDIR) -p $(DESTDIR)/usr/lib
	$(MV) $(DYLIBNAME) $(DESTDIR)/usr/lib
