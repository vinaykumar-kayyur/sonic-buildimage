/**
 @file phy_demo.c
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/
#include "sal.h"
#include "phy_drv_common.h"
#include "phy_drv_api.h"

extern phy_info_t g_phy_port_info[CTC_MAX_PHY_PORT_NUM];

phy_info_t phy_port_info[] = {
    {0,0,1},
    {1,0,2},
    {2,0,3},
    {3,0,4},
    {4,0,5},
    {5,0,6},
    {6,0,7},
    {7,0,8},
};

int main(int argc, char *argv[])
{
    uint32 loop = 0;
    int32 ret = 0;
    uint32  phy_id;
    uint32 port_num = 0;
    phy_manufacturers_t *phy;
    ctc_phy_driver_t *phy_drv=NULL;
    uint32 link_status = 0;

    port_num = sizeof(phy_port_info)/sizeof(phy_info_t);

    /* init port info according to your board  */
    sal_memset(g_phy_port_info, 0, CTC_MAX_PHY_PORT_NUM * sizeof(phy_info_t));
    for (loop = 0; loop < port_num; loop++)
    {
        g_phy_port_info[loop].port_id = phy_port_info[loop].port_id;
        g_phy_port_info[loop].bus = phy_port_info[loop].bus;
        g_phy_port_info[loop].phy_addr = phy_port_info[loop].phy_addr;
        g_phy_port_info[loop].ctl_id = phy_port_info[loop].ctl_id;
    }

    /* init port with phy */
    for (loop = 0; loop < port_num; loop++)
    {
        ret += ctc_phy_init(0,loop);
    }

    /* config port with phy */
    for (loop = 0; loop < port_num; loop++)
    {
        ret += ctc_phy_set_port_en(0,loop,0);
        ret += ctc_phy_set_port_speed(0,loop,CTC_PORT_SPEED_MAX);
        ret += ctc_phy_set_port_duplex(0,loop,GLB_DUPLEX_FULL);
        ret += ctc_phy_set_port_auto_neg(0,loop,1);
        ret += ctc_phy_set_port_en(0,loop,0);
    }

    /* polling port status with phy */
    while(1)
    {
        for (loop = 0; loop < port_num; loop++)
        {
            link_status = 0;/* default link down */
            ret =ctc_phy_get_link_up_status(0,loop,&link_status);
            sal_printf("PHY port %d link %s\n", loop, link_status?"up":"down");
        }
    }
    return ret;
}
