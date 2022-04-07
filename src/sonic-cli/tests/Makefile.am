#INCLUDES = -I $(top_srcdir)

bin_PROGRAMS = tests
DBGFLAGS = -ggdb -DDEBUG

CFLAGS_GTEST =
LDADD_GTEST = -L/usr/src/gtest -lgtest -lgtest_main -lgmock -lgmock_main

tests_SOURCES = main.cpp

tests_CFLAGS = $(DBGFLAGS) $(AM_CFLAGS) $(CFLAGS_COMMON) $(CFLAGS_GTEST)
tests_CPPFLAGS = $(DBGFLAGS) $(AM_CFLAGS) $(CFLAGS_COMMON) $(CFLAGS_GTEST)
tests_LDADD = $(LDADD_GTEST) -lpthread -lswsscommon $(CODE_COVERAGE_LIBS) $(BOOST_PROGRAM_OPTIONS_LIB)