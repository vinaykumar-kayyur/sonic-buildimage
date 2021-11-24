AC_INIT([sonic-eventd],[1.0.0])
AC_CONFIG_SRCDIR([])
AC_CONFIG_AUX_DIR(config)
AM_CONFIG_HEADER(config.h)
AM_INIT_AUTOMAKE([foreign])
AC_LANG_C
AC_LANG([C++])
AC_PROG_CC
AC_PROG_CXX
AC_PROG_LIBTOOL
AC_HEADER_STDC

AC_ARG_ENABLE(debug,
[  --enable-debug      Compile with debugging flags],
[case "${enableval}" in
        yes) debug=true ;;
        no)  debug=false ;;
        *) AC_MSG_ERROR(bad value ${enableval} for --enable-debug) ;;
esac],[debug=false])
AM_CONDITIONAL(DEBUG, test x$debug = xtrue)

AC_ARG_ENABLE(gtest,
[  --enable-gtest       Compile with googletest flags],
[case "${enableval}" in
        yes) gtest=true ;;
        no)  gtest=false ;;
        *) AC_MSG_ERROR(bad value ${enableval} for --enable-gtest) ;;
esac],[gtest=false])
AM_CONDITIONAL(GTEST, test x$gtest = xtrue)

CFLAGS_COMMON="-std=c++11 -Wall -fPIC -Wno-write-strings -I/usr/include/swss -I/usr/include"

CFLAGS_COMMON+=" -Werror"

AC_SUBST(CFLAGS_COMMON)

dnl ---------------
dnl dlopen & dlinfo
dnl ---------------
AC_SEARCH_LIBS([dlopen], [dl dld], [], [
  AC_MSG_ERROR([unable to find the dlopen()])
])

AC_CONFIG_FILES([
    src/Makefile
    Makefile
])

AC_OUTPUT

