/*
 * Copyright (C) 2009-2018 Realtek Semiconductor Corp.
 * All Rights Reserved.
 *
 * This program is the proprietary software of Realtek Semiconductor
 * Corporation and/or its licensors, and only be used, duplicated,
 * modified or distributed under the authorized license from Realtek.
 *
 * ANY USE OF THE SOFTWARE OTHER THAN AS AUTHORIZED UNDER
 * THIS LICENSE OR COPYRIGHT LAW IS PROHIBITED.
 *
 * Revision:
 * Date: 2018-06-15
 *
 * Purpose : PHY Init module.
 *
 * Feature : This Module is used to initial the separate PHY driver.
 *
 */

#include <common/rt_type.h>
#include <common/rt_error.h>
#include <common/debug/rt_log.h>
#include <hal/chipdef/driver.h>
#include <hal/common/halctrl.h>
#include <hal/phy/identify.h>
#include <hal/phy/phy_probe.h>
#include <hal/phy/phy_construct.h>
#include <phy/inc/util/phy_wrapped_miim.h>
#include <phy/inc/phy_hal.h>
#include <phy/inc/util/phy_waMon.h>
#include <dal/dal_mgmt.h>
#include <dal/dal_phy.h>

#include <phy_init.h>
#include <osal/lib.h>
#include <osal/memory.h>
#include <hwp/hwp_util.h>

extern hwp_hwProfile_t phy_driver_hwp;

int32 rtk_inited_g;
int32 dev_autoneg_off_g;

static int32 port_phy_info_g[PORT_MAX_BUS_ID][PORT_MAX_PHY_ADDR];

struct port_eye_param_s {
    int port;
    int value;
};
typedef struct port_eye_param_s port_eye_param_t;

port_eye_param_t port_eye_conf_48e4t[] = {
    {.port = 0 , .value = 0x1c1e00},
    {.port = 4 , .value = 0x101600},
    {.port = 16, .value = 0x111500},
    {.port = 20, .value = 0x0e1100},
    {.port = 8 , .value = 0x0f1000},
    {.port = 12, .value = 0x0e0f00},
    {.port = 36, .value = 0x0a0a00},
    {.port = 40, .value = 0x0a0900},
    {.port = 24, .value = 0x000c00},
    {.port = 28, .value = 0x000b00},
    {.port = 52, .value = 0x000b00},
    {.port = 56, .value = 0x000a00},
};

port_eye_param_t port_eye_conf_48e4t_18e[] = {
    {.port = 0 , .value = 0x091000},
    {.port = 4 , .value = 0x0a0e00},
    {.port = 16, .value = 0x080e00},
    {.port = 20, .value = 0x080f00},
    {.port = 8 , .value = 0x091000},
    {.port = 12, .value = 0x090f00},
    {.port = 36, .value = 0x070a00},
    {.port = 40, .value = 0x090900},
    {.port = 24, .value = 0x000900},
    {.port = 28, .value = 0x000900},
    {.port = 52, .value = 0x000700},
    {.port = 56, .value = 0x000700},
};

FILE *cust_rtk_log_f;
phy_hwp_phyDescp_t cust_phy_descp_48g4x[] = {
    [0] = { .chip = RTK_PHYTYPE_RTL8214FC, .mac_id = 0,  .phy_max = 4 },
    [1] = { .chip = RTK_PHYTYPE_RTL8214FC, .mac_id = 4,  .phy_max = 4 },
    [2] = { .chip = RTK_PHYTYPE_RTL8214FC, .mac_id = 16, .phy_max = 4 },
    [3] = { .chip = RTK_PHYTYPE_RTL8214FC, .mac_id = 20, .phy_max = 4 },
    [4] = { .chip = RTK_PHYTYPE_RTL8214FC, .mac_id = 8,  .phy_max = 4 },
    [5] = { .chip = RTK_PHYTYPE_RTL8214FC, .mac_id = 32, .phy_max = 4 },
    [6] = { .chip = RTK_PHYTYPE_RTL8214FC, .mac_id = 36, .phy_max = 4 },
    [7] = { .chip = HWP_END },
};

phy_hwp_portDescp_t cust_port_descp_48g4x[] = {
    [0] =  { .mac_id = 0,    .phy_idx = 0,  .smi = 0,    .phy_addr = 0,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [1] =  { .mac_id = 1,    .phy_idx = 0,  .smi = 0,    .phy_addr = 1,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [2] =  { .mac_id = 2,    .phy_idx = 0,  .smi = 0,    .phy_addr = 2,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [3] =  { .mac_id = 3,    .phy_idx = 0,  .smi = 0,    .phy_addr = 3,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [4] =  { .mac_id = 4,    .phy_idx = 1,  .smi = 0,    .phy_addr = 8,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [5] =  { .mac_id = 5,    .phy_idx = 1,  .smi = 0,    .phy_addr = 9 ,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [6] =  { .mac_id = 6,    .phy_idx = 1,  .smi = 0,    .phy_addr = 10,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [7] =  { .mac_id = 7,    .phy_idx = 1,  .smi = 0,    .phy_addr = 11,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [8] =  { .mac_id = 16,   .phy_idx = 2,  .smi = 0,    .phy_addr = 16,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [9] =  { .mac_id = 17,   .phy_idx = 2,  .smi = 0,    .phy_addr = 17,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [10] = { .mac_id = 18,   .phy_idx = 2,  .smi = 0,    .phy_addr = 18,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [11] = { .mac_id = 19,   .phy_idx = 2,  .smi = 0,    .phy_addr = 19,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [12] = { .mac_id = 20,   .phy_idx = 3,  .smi = 1,    .phy_addr = 0,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [13] = { .mac_id = 21,   .phy_idx = 3,  .smi = 1,    .phy_addr = 1,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [14] = { .mac_id = 22,   .phy_idx = 3,  .smi = 1,    .phy_addr = 2,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [15] = { .mac_id = 23,   .phy_idx = 3,  .smi = 1,    .phy_addr = 3,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [16] = { .mac_id = 8,    .phy_idx = 4,  .smi = 1,    .phy_addr = 8,     .eth = HWP_GE,   .medi = HWP_COMBO,},
    [17] = { .mac_id = 9,    .phy_idx = 4,  .smi = 1,    .phy_addr = 9 ,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [18] = { .mac_id = 10,   .phy_idx = 4,  .smi = 1,    .phy_addr = 10,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [19] = { .mac_id = 11,   .phy_idx = 4,  .smi = 1,    .phy_addr = 11,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [20] = { .mac_id = 32,   .phy_idx = 5,  .smi = 1,    .phy_addr = 16,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [21] = { .mac_id = 33,   .phy_idx = 5,  .smi = 1,    .phy_addr = 17,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [22] = { .mac_id = 34,   .phy_idx = 5,  .smi = 1,    .phy_addr = 18,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [23] = { .mac_id = 35,   .phy_idx = 5,  .smi = 1,    .phy_addr = 19,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [24] = { .mac_id = 36,   .phy_idx = 6,  .smi = 1,    .phy_addr = 24,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [25] = { .mac_id = 37,   .phy_idx = 6,  .smi = 1,    .phy_addr = 25,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [26] = { .mac_id = 38,   .phy_idx = 6,  .smi = 1,    .phy_addr = 26,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [27] = { .mac_id = 39,   .phy_idx = 6,  .smi = 1,    .phy_addr = 27,    .eth = HWP_GE,   .medi = HWP_COMBO,},
    [28] = { .mac_id = HWP_END },
};

phy_hwp_phyDescp_t cust_phy_descp_48e4x_18e[] = {
    [0] = { .chip = RTK_PHYTYPE_RTL8218E, .mac_id = 0,   .phy_max = 8 },
    [1] = { .chip = RTK_PHYTYPE_RTL8218E, .mac_id = 16,  .phy_max = 8 },
    [2] = { .chip = RTK_PHYTYPE_RTL8218E, .mac_id = 8,   .phy_max = 8 },
    [3] = { .chip = RTK_PHYTYPE_RTL8218E, .mac_id = 36,  .phy_max = 8 },
    [4] = { .chip = RTK_PHYTYPE_RTL8218E, .mac_id = 24,  .phy_max = 8 },
    [5] = { .chip = RTK_PHYTYPE_RTL8218E, .mac_id = 52,  .phy_max = 8 },
    [6] = { .chip = HWP_END },
};

phy_hwp_phyDescp_t cust_phy_descp_48e4x[] = {
    [0] = { .chip = RTK_PHYTYPE_RTL8218D, .mac_id = 0,   .phy_max = 8 },
    [1] = { .chip = RTK_PHYTYPE_RTL8218D, .mac_id = 16,  .phy_max = 8 },
    [2] = { .chip = RTK_PHYTYPE_RTL8218D, .mac_id = 8,   .phy_max = 8 },
    [3] = { .chip = RTK_PHYTYPE_RTL8218D, .mac_id = 36,  .phy_max = 8 },
    [4] = { .chip = RTK_PHYTYPE_RTL8218D, .mac_id = 24,  .phy_max = 8 },
    [5] = { .chip = RTK_PHYTYPE_RTL8218D, .mac_id = 52,  .phy_max = 8 },
    [6] = { .chip = HWP_END },
};

phy_hwp_portDescp_t cust_port_descp_48e4x[] = {
    [0] =  { .mac_id = 0,    .phy_idx = 0,  .smi = 0,    .phy_addr = 0,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [1] =  { .mac_id = 1,    .phy_idx = 0,  .smi = 0,    .phy_addr = 1,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [2] =  { .mac_id = 2,    .phy_idx = 0,  .smi = 0,    .phy_addr = 2,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [3] =  { .mac_id = 3,    .phy_idx = 0,  .smi = 0,    .phy_addr = 3,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [4] =  { .mac_id = 4,    .phy_idx = 0,  .smi = 0,    .phy_addr = 4,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [5] =  { .mac_id = 5,    .phy_idx = 0,  .smi = 0,    .phy_addr = 5,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [6] =  { .mac_id = 6,    .phy_idx = 0,  .smi = 0,    .phy_addr = 6,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [7] =  { .mac_id = 7,    .phy_idx = 0,  .smi = 0,    .phy_addr = 7,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [8] =  { .mac_id = 16,   .phy_idx = 1,  .smi = 0,    .phy_addr = 8,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [9] =  { .mac_id = 17,   .phy_idx = 1,  .smi = 0,    .phy_addr = 9 ,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [10] = { .mac_id = 18,   .phy_idx = 1,  .smi = 0,    .phy_addr = 10,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [11] = { .mac_id = 19,   .phy_idx = 1,  .smi = 0,    .phy_addr = 11,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [12] = { .mac_id = 20,   .phy_idx = 1,  .smi = 0,    .phy_addr = 12,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [13] = { .mac_id = 21,   .phy_idx = 1,  .smi = 0,    .phy_addr = 13,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [14] = { .mac_id = 22,   .phy_idx = 1,  .smi = 0,    .phy_addr = 14,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [15] = { .mac_id = 23,   .phy_idx = 1,  .smi = 0,    .phy_addr = 15,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [16] = { .mac_id = 8,    .phy_idx = 2,  .smi = 0,    .phy_addr = 16,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [17] = { .mac_id = 9,    .phy_idx = 2,  .smi = 0,    .phy_addr = 17,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [18] = { .mac_id = 10,   .phy_idx = 2,  .smi = 0,    .phy_addr = 18,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [19] = { .mac_id = 11,   .phy_idx = 2,  .smi = 0,    .phy_addr = 19,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [20] = { .mac_id = 12,   .phy_idx = 2,  .smi = 0,    .phy_addr = 20,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [21] = { .mac_id = 13,   .phy_idx = 2,  .smi = 0,    .phy_addr = 21,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [22] = { .mac_id = 14,   .phy_idx = 2,  .smi = 0,    .phy_addr = 22,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [23] = { .mac_id = 15,   .phy_idx = 2,  .smi = 0,    .phy_addr = 23,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [24] = { .mac_id = 36,   .phy_idx = 3,  .smi = 1,    .phy_addr = 0,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [25] = { .mac_id = 37,   .phy_idx = 3,  .smi = 1,    .phy_addr = 1,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [26] = { .mac_id = 38,   .phy_idx = 3,  .smi = 1,    .phy_addr = 2,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [27] = { .mac_id = 39,   .phy_idx = 3,  .smi = 1,    .phy_addr = 3,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [28] = { .mac_id = 40,   .phy_idx = 3,  .smi = 1,    .phy_addr = 4,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [29] = { .mac_id = 41,   .phy_idx = 3,  .smi = 1,    .phy_addr = 5,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [30] = { .mac_id = 42,   .phy_idx = 3,  .smi = 1,    .phy_addr = 6,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [31] = { .mac_id = 43,   .phy_idx = 3,  .smi = 1,    .phy_addr = 7,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [32] = { .mac_id = 24,   .phy_idx = 4,  .smi = 1,    .phy_addr = 8 ,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [33] = { .mac_id = 25,   .phy_idx = 4,  .smi = 1,    .phy_addr = 9 ,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [34] = { .mac_id = 26,   .phy_idx = 4,  .smi = 1,    .phy_addr = 10,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [35] = { .mac_id = 27,   .phy_idx = 4,  .smi = 1,    .phy_addr = 11,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [36] = { .mac_id = 28,   .phy_idx = 4,  .smi = 1,    .phy_addr = 12,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [37] = { .mac_id = 29,   .phy_idx = 4,  .smi = 1,    .phy_addr = 13,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [38] = { .mac_id = 30,   .phy_idx = 4,  .smi = 1,    .phy_addr = 14,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [39] = { .mac_id = 31,   .phy_idx = 4,  .smi = 1,    .phy_addr = 15,     .eth = HWP_GE,   .medi = HWP_COPPER,},
    [40] = { .mac_id = 52,   .phy_idx = 5,  .smi = 1,    .phy_addr = 16,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [41] = { .mac_id = 53,   .phy_idx = 5,  .smi = 1,    .phy_addr = 17,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [42] = { .mac_id = 54,   .phy_idx = 5,  .smi = 1,    .phy_addr = 18,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [43] = { .mac_id = 55,   .phy_idx = 5,  .smi = 1,    .phy_addr = 19,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [44] = { .mac_id = 56,   .phy_idx = 5,  .smi = 1,    .phy_addr = 20,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [45] = { .mac_id = 57,   .phy_idx = 5,  .smi = 1,    .phy_addr = 21,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [46] = { .mac_id = 58,   .phy_idx = 5,  .smi = 1,    .phy_addr = 22,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [47] = { .mac_id = 59,   .phy_idx = 5,  .smi = 1,    .phy_addr = 23,    .eth = HWP_GE,   .medi = HWP_COPPER,},
    [48] = { .mac_id = HWP_END },
};

hal_control_t   phy_hal_ctrl[RTK_MAX_NUM_OF_UNIT];

dal_mgmt_info_t     *pMgmt_node[1];

/* driver service APIs */
rt_macdrv_t phyMiiDrv =
{
    .fMdrv_init                             = NULL,
    .fMdrv_miim_read                        = wrapped_miim_read,
    .fMdrv_miim_write                       = wrapped_miim_write,
    .fMdrv_miim_park_read                   = wrapped_miim_park_read,
    .fMdrv_miim_park_write                  = wrapped_miim_park_write,
    .fMdrv_miim_broadcast_write             = NULL,
    .fMdrv_miim_extParkPage_read            = NULL,
    .fMdrv_miim_extParkPage_write           = NULL,
    .fMdrv_miim_extParkPage_portmask_write  = NULL,
    .fMdrv_miim_mmd_read                    = wrapped_mmd_read,
    .fMdrv_miim_mmd_write                   = wrapped_mmd_write,
    .fMdrv_miim_mmd_portmask_write          = NULL,
    .fMdrv_table_read                       = NULL,
    .fMdrv_table_write                      = NULL,
    .fMdrv_port_probe                       = NULL,
    .fMdrv_miim_portmask_write              = NULL,
    .fMdrv_miim_pollingEnable_get           = wrapped_miim_pollingEnable_get,
    .fMdrv_miim_pollingEnable_set           = wrapped_miim_pollingEnable_set,
    .fMdrv_mac_serdes_rst                   = NULL,
    .fMdrv_mac_serdes_read                  = NULL,
    .fMdrv_mac_serdes_write                 = NULL,
    .fMdrv_smi_read                         = NULL,
    .fMdrv_smi_write                        = NULL,
    .fMdrv_miim_portSmiMdxProto_get         = phy_hal_miim_portSmiMdxProto_get,
    .fMdrv_miim_portSmiMdxProto_set         = phy_hal_miim_portSmiMdxProto_set,
}; /* end of phyMiiDrv */

/* Function Name:
 *      phy_hwp_init
 * Description:
 *      fill HWP port and phy structure with customer's configuration.
 * Input:
 *      profile  - HWP pointer.
 * Output:
 *      None
 * Return:
 *      None
 * Note:
 *      None
 */
void phy_hwp_init(phy_hwp_portDescp_t *portDesc, phy_hwp_phyDescp_t  *phyDesc)
{
    int32   scan_idx;
    int32   empty_idx = 0;

    hwp_hwProfile_t *profile;

    profile = &phy_driver_hwp;
    if ((portDesc == NULL) || (phyDesc == NULL))
    {
        return;
    }

    for (scan_idx = 0; scan_idx < RTK_MAX_PORT_PER_UNIT; scan_idx++)
    {
        if (empty_idx == 0)
        {
            if (portDesc[scan_idx].mac_id != HWP_END)
            {
                profile->swDescp[0]->port.descp[scan_idx].mac_id = portDesc[scan_idx].mac_id;
                profile->swDescp[0]->port.descp[scan_idx].phy_idx = portDesc[scan_idx].phy_idx;
                profile->swDescp[0]->port.descp[scan_idx].eth = portDesc[scan_idx].eth;
                profile->swDescp[0]->port.descp[scan_idx].medi = portDesc[scan_idx].medi;
                profile->swDescp[0]->port.descp[scan_idx].attr = HWP_ETH;
                profile->swDescp[0]->port.descp[scan_idx].smi = portDesc[scan_idx].smi;
                profile->swDescp[0]->port.descp[scan_idx].phy_addr = portDesc[scan_idx].phy_addr;
            }
            else
            {
                empty_idx = 1;
                profile->swDescp[0]->port.descp[scan_idx].mac_id = HWP_END;
            }
        }
        else
        {
            osal_memset(&profile->swDescp[0]->port.descp[scan_idx], 0, sizeof(hwp_portDescp_t));
        }
    }

    empty_idx = 0;
    for (scan_idx = 0; scan_idx < RTK_MAX_PHY_PER_UNIT; scan_idx++)
    {
        if (empty_idx == 0)
        {
            if (phyDesc[scan_idx].chip != HWP_END)
            {
                profile->swDescp[0]->phy.descp[scan_idx].chip = phyDesc[scan_idx].chip;
                profile->swDescp[0]->phy.descp[scan_idx].phy_max = phyDesc[scan_idx].phy_max;
                profile->swDescp[0]->phy.descp[scan_idx].mac_id = phyDesc[scan_idx].mac_id;

            }
            else
            {
                empty_idx = 1;
                profile->swDescp[0]->phy.descp[scan_idx].chip = HWP_END;
            }
        }
        else
        {
            osal_memset(&profile->swDescp[0]->phy.descp[scan_idx], 0, sizeof(hwp_phyDescp_t));
        }
    }

    hwp_myHwProfile = profile;
    hwp_myHwProfile->parsed_info = &parsedInfoEmpty;
    hwp_init(NULL);

    return;
}

/* Function Name:
 *      _rtk_phy_hal_ctrl_init
 * Description:
 *      Init PHY HAL
 * Input:
 *      None
 * Output:
 *      None
 * Return:
 *      RT_ERR_OK     - OK
 *      RT_ERR_FAILED - Failed
 * Note:
 *      None
 */
int32
_rtk_phy_hal_ctrl_init(uint32 unit)
{
    rt_driver_t     *pChip_driver;

    if (unit >= RTK_MAX_NUM_OF_UNIT)
    {
        return RT_ERR_UNIT_ID;
    }

    osal_memset(&phy_hal_ctrl[unit], 0, sizeof(hal_control_t));

    phy_hal_ctrl[unit].miim_sem = osal_sem_mutex_create();

    if ((pChip_driver = osal_alloc(sizeof(rt_driver_t))) == NULL)
    {
        return RT_ERR_MEM_ALLOC;
    }
    osal_memset(pChip_driver, 0, sizeof(rt_driver_t));

    /* hook MDC/MDIO driver */
    pChip_driver->pMacdrv = &phyMiiDrv;

    phy_hal_ctrl[unit].pChip_driver = pChip_driver;

    phy_hal_ctrl[unit].chip_flags |= HAL_CHIP_ATTACHED;

    return RT_ERR_OK;
}

/* Function Name:
 *      rtk_init
 * Description:
 *      Init RTK
 * Input:
 *      None
 * Output:
 *      None
 * Return:
 *      RT_ERR_OK     - OK
 *      RT_ERR_FAILED - Failed
 * Note:
 *      None
 */
int32
rtk_init(rtk_phy_initInfo_t *pInitInfo)
{
    int32   ret;
    uint32  unit;

    pMgmt_node[0] = (dal_mgmt_info_t *)osal_alloc(sizeof(dal_mgmt_info_t));
    if (NULL == pMgmt_node[0])
    {
        return RT_ERR_MEM_ALLOC;
    }
    osal_memset(pMgmt_node[0], 0, sizeof(dal_mgmt_info_t));
    pMgmt_node[0]->pMapper = (dal_mapper_t *)osal_alloc(sizeof(dal_mapper_t));
    if (NULL == pMgmt_node[0]->pMapper)
    {
        return RT_ERR_MEM_ALLOC;
    }
    osal_memset(pMgmt_node[0]->pMapper, 0, sizeof(dal_mapper_t));

    phy_hwp_init(pInitInfo->port_desc, pInitInfo->phy_desc);

    phy_identify_init();

    HWP_UNIT_TRAVS_LOCAL(unit)
    {
        if ((ret = _rtk_phy_hal_ctrl_init(unit)) != RT_ERR_OK)
        {
            return ret;
        }
    }

    HWP_UNIT_TRAVS_LOCAL(unit)
    {
        /* Probe PHY */
        phy_probe(unit);

        /* Construct PHY */
        phy_construct_config_init(unit);

        /* Init PHY */
        phy_init(unit);

        /* Init PHY module */
        dal_phyMapper_init(pMgmt_node[0]->pMapper);
        pMgmt_node[0]->pMapper->phy_init(unit);
    }

    dal_waMon_init();

    dal_waMon_enable();

    return RT_ERR_OK;
}

int32 cust_get_machine_id(void)
{
    FILE *fp;
    char buf[MAX_LINE_LEN];
    int32 cust_cur_dev;

    fp = fopen(MACHINE_FILE, "r");
    if (!fp) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "machine file:%s open fail\n", MACHINE_FILE);
        return -1;
    }

    memset(buf, 0, MAX_LINE_LEN);
    while (fgets(buf, MAX_LINE_LEN, fp)) {
        if (!strncmp(buf, "onie_platform=", strlen("onie_platform="))) {
            break;
        }
    }
    if (!strncmp(buf, "onie_platform=arm64-ragile_ra-b6010-48gt4x-r0",
                     strlen("onie_platform=arm64-ragile_ra-b6010-48gt4x-r0"))) {
        cust_cur_dev = DEV_48E4X;
    } else if (!strncmp(buf, "onie_platform=arm64-ragile_ra-b6010-48gt4x-r-r0",
                     strlen("onie_platform=arm64-ragile_ra-b6010-48gt4x-r-r0"))) {
        cust_cur_dev = DEV_48E4X;
    } else {
        cust_cur_dev = -1;  /* invalid device */
    }
    fclose(fp);

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "cur_dev:%d\n", cust_cur_dev);
    return cust_cur_dev;
}

int32 cust_get_ctc_port_info(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 *unit, uint32 *port)
{
    if (!rtk_inited_g) {
        return RT_ERR_FAILED;
    }

    if (port_phy_info_g[param->bus][param->phy_addr] < 0) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "get port info fail, param->phy_addr:%d param->bus:%d\n", param->phy_addr, param->bus);
        return RT_ERR_FAILED;
    }

    *unit = lchip;
    *port = port_phy_info_g[param->bus][param->phy_addr];
    return RT_ERR_OK;
}

int32 cust_rtk_get_base_port(uint32 unit, uint32 port, uint32 *base_port)
{
    if (!HWP_PORT_EXIST(unit, port)) {
        return RT_ERR_FAILED;
    }

    *base_port = HWP_PHY_BASE_MACID(unit, port);
    return RT_ERR_OK;
}

int32 cust_rtk_get_port_serdes_id(uint32 unit, uint32 port, uint32 *serdes_id)
{
    uint32 base_port;

    if (!HWP_PORT_EXIST(unit, port)) {
        return RT_ERR_FAILED;
    }

    base_port = HWP_PHY_BASE_MACID(unit, port);
    /* 1 serdes 4 port */
    if (port - base_port >= 4) {
        *serdes_id = 1;
    } else {
        *serdes_id = 0;
    }

    return RT_ERR_OK;
}

int32 cust_rtk_init(int unit)
{
    rtk_phy_initInfo_t initInfo;
    int32 ret;
    uint32 port, val;
    int32 port_num, i, j;
    phy_hwp_portDescp_t *phy_desc;
    rtk_sds_eyeParam_t eye_p;
    int rv;
    uint32 value;
    uint32 base_port, sdsid;
    ctc_chip_mdio_para_t para;
    int32 cust_cur_dev;

    if (rtk_inited_g) {
        return RT_ERR_OK;
    }

    if (!cust_rtk_log_f) {
        cust_rtk_log_f = fopen(CUST_RTK_LOG_FILE_DIR, "w");
        if (!cust_rtk_log_f) {
            printf("open rtk log file fail\n");
        }
    }

    ret = cust_phy_mdio_init();
    if (ret) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "reg mdio interface fail\n");
        return RT_ERR_FAILED;
    }
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "reg mdio interface success\n");

    cust_cur_dev = cust_get_machine_id();

    /* current not support multi units, reserved for subsequent use */
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "rtk cur unit:%d\n", unit);

    switch (cust_cur_dev) {
    case DEV_48G4X:
        initInfo.port_desc = cust_port_descp_48g4x;
        initInfo.phy_desc = cust_phy_descp_48g4x;
        phy_desc = cust_port_descp_48g4x;
        port_num = sizeof(cust_port_descp_48g4x) / sizeof(cust_port_descp_48g4x[0]) - 1;
        break;
    case DEV_48E4X:
        /* reg 3 val 0xc984 is 8218e. for now, we trust bus0 phyaddr0 info */
        memset(&para, 0, sizeof(ctc_chip_mdio_para_t));
        para.reg = 3;
        para.ctl_id = 0;    /* always 0, for now */
        para.bus = 0;
        para.phy_addr = 0;
        rv = cust_phy_mdio_read(0, CTC_CHIP_MDIO_GE, &para);
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "48e dev reg 3 read, val:0x%x rv:%d\n", para.value, rv);
        if (para.value == 0xc984) {
            initInfo.phy_desc = cust_phy_descp_48e4x_18e;
            dev_autoneg_off_g = 1;
        } else {
            initInfo.phy_desc = cust_phy_descp_48e4x;
        }
        initInfo.port_desc = cust_port_descp_48e4x;
        phy_desc = cust_port_descp_48e4x;
        port_num = sizeof(cust_port_descp_48e4x) / sizeof(cust_port_descp_48e4x[0]) - 1;
        break;
    default:
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "invalid cust_cur_dev:%d, exist rtk init\n", cust_cur_dev);
        return RT_ERR_TYPE;
    }

    /* init global port phy info */
    for (i = 0; i < PORT_MAX_BUS_ID; i++) {
        for (j = 0; j < PORT_MAX_PHY_ADDR; j++) {
            port_phy_info_g[i][j] = -1;
        }
    }
    for (i = 0; i < port_num; i++) {
        port_phy_info_g[phy_desc[i].smi][phy_desc[i].phy_addr] = phy_desc[i].mac_id;
    }
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "total %d ports info inited\n", port_num);

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "rtk cust_cur_dev:%d start init...\n", cust_cur_dev);
    ret = rtk_init(&initInfo);
    (void)hwp_parsedInfo_show(unit);
    if (ret) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "cust_rtk_init fail\n");
        return ret;
    }
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "cust_rtk_init ok\n");

    switch (cust_cur_dev) {
    case DEV_48G4X:
        HWP_PORT_TRAVS_EXCEPT_CPU(unit, port) {
            ret = rtk_port_phyComboPortMedia_set(unit, port, PORT_MEDIA_FIBER);
            if (ret) {
                CUST_RTK_LOG(CUST_RT_LOG_ERR, "rtk_port_phyComboPortMedia_set PORT_MEDIA_FIBER fail, u:%d p:%d ret:%d\n", unit, port, ret);
            } else {
                CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "rtk_port_phyComboPortMedia_set PORT_MEDIA_FIBER success, u:%d p:%d\n", unit, port);
            }
        }

        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "start write reg avoid shaking...\n");
        HWP_PORT_TRAVS_EXCEPT_CPU(unit, port) {
            if (port == HWP_PHY_BASE_MACID(unit, port)) {
                cust_rtk_mdio_write(unit, port, 0, 30, 8);
                cust_rtk_mdio_read(unit, port, 0x465, 0x12, &val);
                cust_rtk_mdio_write(unit, port, 0, 30, 0);
                if (val == 0x4007) {
                    cust_rtk_mdio_write(unit, port, 0, 30, 8);
                    cust_rtk_mdio_write(unit, port, 0x465, 0x12, 0x40f7 );
                    cust_rtk_mdio_read(unit, port, 0x465, 0x12, &val);
                    cust_rtk_mdio_write(unit, port, 0, 30, 0);
                }
                CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "u:%d p:%d read Page 0x465, Reg 0x12 val: 0x%x\n", unit, port, val);
            }
        }
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "end write reg avoid shaking...\n");

        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "start write tx amp for phy to module...\n");
        HWP_PORT_TRAVS_EXCEPT_CPU(unit, port) {
            cust_rtk_mdio_write(unit, port, 0, 29, 3);
            cust_rtk_mdio_write(unit, port, 0xd, 0x10, 0x1100);
            cust_rtk_mdio_read(unit, port, 0xd, 0x10, &val);
            cust_rtk_mdio_write(unit, port, 0, 29, 0);
            CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "u:%d p:%d read Page 0xd, Reg 0x10 val: 0x%x\n", unit, port, val);
        }
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "end write tx amp for phy to module\n");
        break;
    case DEV_48E4X:
        /* import ffe params */
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "ffe size %d\n", sizeof(port_eye_conf_48e4t) / sizeof(port_eye_conf_48e4t[0]));
        for (i = 0; i < sizeof(port_eye_conf_48e4t) / sizeof(port_eye_conf_48e4t[0]); i++) {
            port = port_eye_conf_48e4t[i].port;
            value = port_eye_conf_48e4t[i].value;
            if (dev_autoneg_off_g) {
                value = port_eye_conf_48e4t_18e[i].value;
            }

            memset(&eye_p, 0, sizeof(rtk_sds_eyeParam_t));
            rv = cust_rtk_get_port_serdes_id(unit, port, &sdsid);
            if (rv) {
                CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d get_port_serdes_id fail, rv:%d\n",
                    unit, port, rv);
                return rv;
            }


            eye_p.pre_en = 1;
            eye_p.pre_amp = value & 0xff;
            eye_p.main_en = 1;
            eye_p.main_amp = (value & 0xff00) >> 8;
            eye_p.post_en = 1;
            eye_p.post_amp = (value & 0xff0000) >> 16;

            CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "port:%d eye %d %d %d\n", port, eye_p.pre_amp, eye_p.main_amp, eye_p.post_amp);
            rv = cust_rtk_get_base_port(unit, port, &base_port);
            if (rv) {
                CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d get_base_port fail, rv:%d\n",
                    unit, port, rv);
                return rv;
            }

            rv = rtk_port_phySdsEyeParam_set(unit, base_port, sdsid, &eye_p);
            if (rv) {
                CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d base_port:%d sdsid:%d phySdsEyeParam_set fail, rv:%d\n",
                    unit, base_port, sdsid, rv);
                return rv;
            }
        }

        if (dev_autoneg_off_g) {
            HWP_PORT_TRAVS_EXCEPT_CPU(unit, port) {
                if (port == HWP_PHY_BASE_MACID(unit, port)) {
                    cust_rtk_mdio_write(unit, port, 0, 30, 8);
                    cust_rtk_mdio_write(unit, port, 0x400, 0x12, 0x71d0);
                    cust_rtk_mdio_read(unit, port, 0x400, 0x12, &val);
                    cust_rtk_mdio_write(unit, port, 0x500, 0x12, 0x71d0);
                    cust_rtk_mdio_read(unit, port, 0x500, 0x12, &val);
                    cust_rtk_mdio_write(unit, port, 0, 30, 0);
                    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "u:%d p:%d end write reg force off autoneg\n", unit, port);
                }
            }
        }
        break;
    default:
        break;
    }

    rtk_inited_g = 1;

    return RT_ERR_OK;
}
