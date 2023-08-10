/**
 @file phy_platformroutines.c
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/
#include "sal.h"

void ctc_sal_udelay(uint32 usec)
{
    struct timeval tv;

    tv.tv_sec = (time_t) (usec / 1000000);
    tv.tv_usec = (long) (usec % 1000000);
    select(0, NULL, NULL, NULL, &tv);
}

void ctc_sal_delay(uint32 sec)
{
    sleep(sec);
}
