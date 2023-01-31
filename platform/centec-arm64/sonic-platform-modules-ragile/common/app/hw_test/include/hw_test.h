/**
 * Copyright(C) 2010 Ragile Network. All rights reserved.
 */
/*
 * hw_test.h
 * Original Author : support@ragilenetworks.com, 2012-07-26
 *
 * HardWare test definitions
 *
 * History
 *    v1.0    enbo liang(support@ragilenetworks.com)  2012-07-26  Initial version.
 */
#ifndef _HW_TEST_H
#define _HW_TEST_H

struct hw_applet {
    const char *name;
    const char *help;
    int (*main) (int argc, char **argv);
};

#define HWTEST_APPLET(a, b) {#a, b, a##_main}

extern int hw_help_main(int argc, char **argv);

#endif /* _HW_TEST_H */

