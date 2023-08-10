/**
 @file phy_drv_common.c
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/
#include "sal.h"
#include "phy_drv_def.h"
#include "phy_drv_common.h"
#include "phy_drv_api.h"

int8 g_phy_debug_on = 0;

void phy_debug_enable(uint8 value)
{
    g_phy_debug_on = value;
}

ctc_port_speed_t
phy_speed_glb2ctc(glb_port_speed_t speed)
{
    switch (speed)
    {
        case GLB_SPEED_10M:
            return CTC_PORT_SPEED_10M;
        case GLB_SPEED_100M:
            return CTC_PORT_SPEED_100M;
        case GLB_SPEED_1G:
            return CTC_PORT_SPEED_1G;
        case GLB_SPEED_2_5G:
            return CTC_PORT_SPEED_2G5;
#if (defined DUET2) || (defined TSINGMA)
        case GLB_SPEED_5G:
            return CTC_PORT_SPEED_5G;
#endif
        case GLB_SPEED_10G:
            return CTC_PORT_SPEED_10G;
        case GLB_SPEED_40G:
            return CTC_PORT_SPEED_40G;
#if (defined DUET2) || (defined TSINGMA)
        case GLB_SPEED_25G:
            return CTC_PORT_SPEED_25G;
        case GLB_SPEED_50G:
            return CTC_PORT_SPEED_50G;
#endif
        case GLB_SPEED_100G:
            return CTC_PORT_SPEED_100G;
        default:
            return CTC_PORT_SPEED_MAX;
    }
}

glb_port_speed_t
phy_speed_ctc2glb(ctc_port_speed_t speed)
{
    switch (speed)
    {
        case CTC_PORT_SPEED_10M:
            return GLB_SPEED_10M;
        case CTC_PORT_SPEED_100M:
            return GLB_SPEED_100M;
        case CTC_PORT_SPEED_1G:
            return GLB_SPEED_1G;
        case CTC_PORT_SPEED_2G5:
            return GLB_SPEED_2_5G;
#if (defined DUET2) || (defined TSINGMA)
        case CTC_PORT_SPEED_5G:
            return GLB_SPEED_5G;
#endif
        case CTC_PORT_SPEED_10G:
            return GLB_SPEED_10G;
        case CTC_PORT_SPEED_40G:
            return GLB_SPEED_40G;
#if (defined DUET2) || (defined TSINGMA)
        case CTC_PORT_SPEED_25G:
            return GLB_SPEED_25G;
        case CTC_PORT_SPEED_50G:
            return GLB_SPEED_50G;
#endif
        case CTC_PORT_SPEED_100G:
            return GLB_SPEED_100G;
        default:
            return GLB_SPEED_MAX;
    }
}

char *
phy_port_speed_str(ctc_port_speed_t speed)
{
    switch (speed)
    {
        case CTC_PORT_SPEED_10M:
            return "10M";
        case CTC_PORT_SPEED_100M:
            return "100M";
        case CTC_PORT_SPEED_1G:
            return "1G";
        case CTC_PORT_SPEED_2G5:
            return "2.5G";
#ifdef USW
        case CTC_PORT_SPEED_5G:
            return "5G";
#endif
        case CTC_PORT_SPEED_10G:
            return "10G";
        case CTC_PORT_SPEED_40G:
            return "40G";
#ifdef USW
        case CTC_PORT_SPEED_25G:
            return "25G";
        case CTC_PORT_SPEED_50G:
            return "50G";
#endif
        case CTC_PORT_SPEED_100G:
            return "100G";
        case CTC_PORT_SPEED_MAX:
            return "ALL";
        default:
            return "NO";
    }
}

char *
phy_port_interface_str(glb_mac_interface_t if_type)
{
    switch (if_type)
    {
        case GLB_MAC_INTERFACE_SGMII:
            return "SGMII";
        case GLB_MAC_INTERFACE_RGMII:
            return "RGMII";
        case GLB_MAC_INTERFACE_QSGMII:
            return "QSGMII";
        default:
            return "-";
    }
}

int32 ctc_phy_common_unsupport(void)
{
    return CTC_E_FEATURE_NOT_SUPPORT;
}

int32
ctc_phy_common_probe_id(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* id)
{
    int32   ret;
    uint32  phy_id;
    param->reg = PHY_IDENTIFIER1_REG;
    ret = ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common probe id_reg_2 fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }
    phy_id = param->value;
    param->reg = PHY_IDENTIFIER2_REG;
    ret = ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common probe id_reg_1, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }
    *id = phy_id<<16|param->value;
    return ret;
}

uint32
ctc_phy_common_get_port_id(phy_info_t * phy_info, ctc_chip_mdio_para_t* param)
{
    uint32 port_id = 0;
    uint32 index = 0;
    bool found;

    found = 0;
    for (index = 0; index < CTC_MAX_PHY_PORT_NUM; index++)
    {
        if((phy_info[index].bus == param->bus)
            &&(phy_info[index].phy_addr == param->phy_addr))
        {
            /* return index, prevent coverage issues
             * port_id = phy_info[index].port_id;
             */
            port_id = index;
            found = 1;
            break;
        }
    }

    if (!found) {
        PHY_LOG_ERR("bus:%d addr:%d invalid!\n", param->bus, param->phy_addr);
    }
    return port_id;
}

uint32
ctc_phy_common_get_base_addr(phy_info_t * phy_info, ctc_chip_mdio_para_t* param)
{
    uint32 base_port = 0;
    uint16 index = 0;
    for (index = 0; index < CTC_MAX_PHY_PORT_NUM; index++)
    {
        if((phy_info[index].bus == param->bus)
            &&(phy_info[index].phy_addr == param->phy_addr))
        {
            base_port = phy_info[index].phy_base_port;
        }
    }
    return phy_info[base_port].phy_addr;
}

uint8
ctc_phy_common_get_mdio_bus_by_port(phy_info_t * phy_info, uint32 gport)
{
    uint8 bus = 0;
    uint32 index = 0;
    for (index = 0; index < CTC_MAX_PHY_PORT_NUM; index++)
    {
        if (phy_info[index].port_id == gport)
        {
            bus = phy_info[index].bus;
        }
    }
    return bus;
}

uint8
ctc_phy_common_get_chip_by_port(phy_info_t * phy_info, uint32 gport)
{
    uint8 chip_id = 0;
    uint32 index = 0;
    for (index = 0; index < CTC_MAX_PHY_PORT_NUM; index++)
    {
        if (phy_info[index].port_id == gport)
        {
            chip_id = phy_info[index].phy_chip_id;
        }
    }
    return chip_id;
}

uint32
ctc_phy_common_get_base_by_chip(phy_info_t * phy_info, uint8 chip)
{
    uint32 base_id = 0;
    uint32 index = 0;
    for (index = 0; index < CTC_MAX_PHY_PORT_NUM; index++)
    {
        if (phy_info[index].phy_chip_id == chip)
        {
            base_id = phy_info[index].phy_base_port;
        }
    }
    return base_id;
}

int32
ctc_phy_common_autoNegoEnable_get(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* enable)
{
    int32   ret;

    param->reg = PHY_CTL_REG;
    ret = ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common  auto-neg get fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }

    if (param->value & AutoNegotiationEnable_MASK)
    {
        *enable = GLB_ENABLE;
    }
    else
    {
        *enable = GLB_DISABLE;
    }

    return ret;
}

int32
ctc_phy_common_autoNegoEnable_set(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32   ret;
    uint16  phyData0;

    param->reg = PHY_CTL_REG;
    ret = ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common auto-nego set fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }
    phyData0 = param->value;
    phyData0 = phyData0 & ~(AutoNegotiationEnable_MASK | RestartAutoNegotiation_MASK);
    phyData0 = phyData0 | ((enable << AutoNegotiationEnable_OFFSET) | (1 << RestartAutoNegotiation_OFFSET));

    param->value = phyData0;
    ret = ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common auto-nego set fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }

    return ret;
}

int32
ctc_phy_common_duplex_get(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* duplex)
{
    int32   ret;

    param->reg = PHY_CTL_REG;
    ret = ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common duplex get fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }

    *duplex = (param->value & DuplexMode_MASK) >> DuplexMode_OFFSET;

    return ret;
}

int32
ctc_phy_common_duplex_set(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 duplex)
{
    int32   ret;
    uint16  phyData0;

    param->reg = PHY_CTL_REG;
    ret = ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common duplex set fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }
    phyData0 = param->value;
    phyData0 = phyData0 & ~(DuplexMode_MASK);
    phyData0 = phyData0 | (duplex << DuplexMode_OFFSET);
    param->value = phyData0;

    ret = ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common duplex set fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }

    return ret;
}

int32
ctc_phy_common_enable_set(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32   ret;
    uint32  phyData;

    param->reg = PHY_CTL_REG;
    ret = ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common enable set fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }
    phyData = param->value;

    if (GLB_ENABLE == enable)
    {
        phyData &= ~(PowerDown_MASK);
    }
    else
    {
        phyData &= ~(PowerDown_MASK);
        phyData |= (1 << PowerDown_OFFSET);
    }
    param->value = phyData;

    ret = ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param);
    if (ret < 0)
    {
        PHY_LOG_ERR("Phy common enable set fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }

    return ret;
}
