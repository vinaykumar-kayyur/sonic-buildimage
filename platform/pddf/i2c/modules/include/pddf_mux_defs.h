/*
 * Copyright 2019 Broadcom. All rights reserved.
 * The term “Broadcom” refers to Broadcom Inc. and/or its subsidiaries.
 *
 * Description:
 *  Platform MUX defines/structures header file
 */

#ifndef __PAL_MUX_DEFS_H__
#define __PAL_MUX_DEFS_H__

/* MUX CLIENT DATA - PLATFORM DATA FOR PSU CLIENT */
typedef struct MUX_DATA
{
    int virt_bus;       // Virtual base bus number of the mux channels
}MUX_DATA;

#endif //__PAL_MUX_DEFS_H__
