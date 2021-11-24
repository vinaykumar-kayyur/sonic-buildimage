INCLUDES = -I ../include 

bin_PROGRAMS = eventd

lib_LTLIBRARIES = libloghandler.la

if DEBUG
DBGFLAGS = -ggdb -DDEBUG
else
#DBGFLAGS = -g -DNDEBUG
DBGFLAGS = -ggdb -DDEBUG
endif

LIB_LOG_HANDLER=libloghandler.la

libloghandler_la_SOURCES = loghandler.cpp
libloghandler_la_LDFLAGS = -version-info 0:0:0

eventd_SOURCES = eventd.cpp eventutils.cpp eventconsume.cpp

#CXXFLAGS += -ffunction-sections -fdata-sections
#eventd_CPPFLAGS = $(DBGFLAGS) $(AM_CFLAGS) $(CFLAGS_COMMON) $(COV_CFLAGS) $(ASAN_CFLAGS) $(CXXFLAGS)
eventd_CPPFLAGS = $(DBGFLAGS) $(AM_CFLAGS) $(CFLAGS_COMMON) $(COV_CFLAGS) $(ASAN_CFLAGS)
eventd_LDADD = -lnl-3 -lhiredis -lswsscommon -leventnotify $(LIB_LOG_HANDLER) $(COV_LDFLAGS) $(ASAN_LDFLAGS)

