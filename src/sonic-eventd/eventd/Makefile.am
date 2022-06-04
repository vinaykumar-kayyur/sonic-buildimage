INCLUDES = -I $(top_srcdir)/lib \
           -I $(top_srcdir)

bin_PROGRAMS = eventd

if DEBUG
DBGFLAGS = -ggdb -DDEBUG
else
DBGFLAGS = -g -DNDEBUG
endif

eventd_sources = eventd.cpp

eventd_CFLAGS = $(DBGFLAGS) $(AM_CFLAGS) $(CFLAGS_COMMON)
eventd_CPPFLAGS = $(DBGFLAGS) $(AM_CFLAGS) $(CFLAGS_COMMON)
eventd_LDADD = -lpthread -lswsscommon -lzmq -lboost_serialization -luuid

