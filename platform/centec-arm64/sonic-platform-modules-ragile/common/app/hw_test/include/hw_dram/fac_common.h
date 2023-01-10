/*
 * Copyright(C) 2013 Ragile Network. All rights reserved. 
 */
/*
 * common.h 
 * Original Author:  support@ragilenetworks.com, 2013-9-25 
 *
 * factroy generial handle of factory test.
 */

#ifndef _FAC_AC_COMMON_H_
#define _FAC_AC_COMMON_H_

#define FAC_TEST_OK                  0
#define FAC_TEST_FAIL                1
#define GRTD_LOG_DEBUG               2
#define GRTD_LOG_ERR                 1
#define GRTD_LOG_NONE                0
#define FAC_MEM_SIZE_BUF_LEN         1024                   /* save the length of the memory size */
#define FAC_MEM_TEST_SIZE            (1024*1024*32)         /* memory test size */
#define FAC_MEM_AUTOTEST_SIZE        (1024*1024*2048ULL)    /* memory test size */
#define FAC_MEM_MAX_SIZE             (1024*1024*4096ULL)    /* memory test size */
#define FAC_MEM_TEST_PAGESIZE        8192                   /* memory test pagesize */
#define FAC_FILENAME_LEN             128                    /* the length of devive name */
#define FAC_FILE_LINE_LEN            128                    /* the length of each line of the file */
#define FAC_FILE_SIZE_LEN            16                     /* the length of the file indicating the size */
#define GRTD_SDRAM_ECC_ERR           1                      /* ECC check error */
#define GRTD_SDRAM_WR_ERR            2                      /* Read and write operation error */
#define GRTD_SDRAM_GET_MEM_SIZE_ERR  3                      /* get memory capacity error */
#define GRTD_SDRAM_UNKNOW_ERR        4                      /* other unknown errors */


extern int platform_fac_dbg;

#define FAC_LOG_DBG(dbg, fmt, arg...)                       \
    do {                                                    \
        if (dbg <= platform_fac_dbg) {                      \
            printf("[FACTORY <%s>:<%d>] " fmt,          \
                 __FUNCTION__, __LINE__, ##arg); \
        }                                                   \
    } while (0)

#endif /* _FAC_AC_COMMON_H_ */

