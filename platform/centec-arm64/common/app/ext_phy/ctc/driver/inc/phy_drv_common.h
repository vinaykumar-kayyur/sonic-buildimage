/**
 @file phy_drv_common.h
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/
#ifndef _PHY_DRV_COMMON_H
#define _PHY_DRV_COMMON_H
#include "ctc_phy_inc.h"
#include "phy_drv_def.h"

/**@defgroup APP_API Application Interface for Phy Driver
* Here is the detail information about all API for phy driver interface.
**/

/**@defgroup DRVTBL Phy driver table
* Here is the driver info for all supported phys. This table will be register to system.
**/

/**@defgroup PROTBL Phy port property define
* Here is description for phy port property.
**/

extern int8 g_phy_debug_on;

#define PANEL_PORT_MAPPING_FILE "./phy_panel_mapping.cfg"
#define PHY_PORT_MAPPING_FILE "./phy_mapping.cfg"
#define PHY_CHIP_CONFIG             "./chip_profile.cfg"

#define PHY_LOG_OUT     sal_printf

//#define PHY_DEBUG
#define PHY_DEBUG_PRINT(fmt, args...)                             \
do {                                                              \
    if(g_phy_debug_on) {                                          \
        PHY_LOG_OUT("[%d]%s()"fmt,__LINE__,__FUNCTION__,##args);  \
    }                                                             \
}while(0);

#define PHY_LOG_ERR(fmt, args...)     PHY_LOG_OUT("<CTCPHY>  ERROR: "fmt, ##args)
#define PHY_LOG_INFO(fmt, args...)     PHY_LOG_OUT("<CTCPHY>  INFO: "fmt, ##args)


void phy_debug_enable(uint8 value);
ctc_port_speed_t phy_speed_glb2ctc(glb_port_speed_t speed);
glb_port_speed_t phy_speed_ctc2glb(ctc_port_speed_t speed);
char * phy_port_speed_str(ctc_port_speed_t speed);
char * phy_port_interface_str(glb_mac_interface_t if_type);

int32 ctc_phy_common_unsupport(void);
int32 ctc_phy_common_probe_id(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* id);
uint32 ctc_phy_common_get_port_id(phy_info_t * phy_info, ctc_chip_mdio_para_t* param);
uint32 ctc_phy_common_get_base_addr(phy_info_t * phy_info, ctc_chip_mdio_para_t* param);
uint32 ctc_phy_common_get_base_by_chip(phy_info_t * phy_info, uint8 chip);
uint8 ctc_phy_common_get_mdio_bus_by_port(phy_info_t * phy_info, uint32 gport);
uint8 ctc_phy_common_get_chip_by_port(phy_info_t * phy_info, uint32 gport);
int32 ctc_phy_common_autoNegoEnable_get(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* enable);
int32 ctc_phy_common_autoNegoEnable_set(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable);
int32 ctc_phy_common_duplex_get(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* duplex);
int32 ctc_phy_common_duplex_set(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 duplex);
int32 ctc_phy_common_enable_set(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable);

#endif /*_PHY_DRV_COMMON_H*/

