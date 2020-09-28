/*
 * $Id: bitop.h,v 1.16 Broadcom SDK $
 * $Copyright: (c) 2017 Broadcom.
 * Broadcom Proprietary and Confidential. All rights reserved.$
 *
 * SDK custom configuration
 */

#ifndef _SDK_CUSTOM_CONFIG_H
#define _SDK_CUSTOM_CONFIG_H

#ifdef BCM_RPC_SUPPORT

#define ATP_RETRY_TIMEOUT_DEFAULT 1000000
#define ATP_RETRY_COUNT_DEFAULT   20
/*
 **       The RPC timeout interval is chosen to be twice the overall ATP
 **       timeout. Since transaction requires two ATP transfers plus some work on
 **       remote unit, the timeout should theoretically be twice the ATP
 **       timeout plus some processing time, but since we use a very long ATP
 **       timeout we ignore the processing time delay.
 */
#define RPC_REPLY_TIMEOUT (2 * ATP_RETRY_TIMEOUT_DEFAULT * ATP_RETRY_COUNT_DEFAULT)
#endif

#endif /* _SDK_CUSTOM_CONFIG_H */
