
INCLUDES = -I ../include 

lib_LTLIBRARIES = libeventnotify.la

if DEBUG
DBGFLAGS = -ggdb -DDEBUG
else
DBGFLAGS = -ggdb -DDEBUG
endif

libeventnotify_la_SOURCES = eventnotify.cpp

libeventnotify_la_CPPFLAGS = $(DBGFLAGS) $(AM_CFLAGS) $(CFLAGS_COMMON) $(COV_CFLAGS) $(ASAN_CFLAGS)
libeventnotify_la_LIBADD = -lhiredis -lswsscommon $(COV_LDFLAGS) $(ASAN_LDFLAGS)
