/**
 @file phy_drv_mars4c.c
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2021-01-21
 @version v1.0
*/
#include "sal.h"
#include "phy_drv_common.h"
#include "phy_drv_api.h"
#include "phy_mars_common.h"

typedef enum
{
    MARS4C_QSGMIIx1_COPPERx4,
    MARS4C_QSGMIIx1_FIBERx4,
    MARS4C_QSGMIIx1_COMBOx4,
    MARS4C_QSGMIIx1_SGMIIx4,
    MARS4C_SGMIIx4_COPPERx4,
} phy_mars4c_mode_t;

extern phy_info_t g_phy_port_info[CTC_MAX_PHY_PORT_NUM];

/*****************************************************************************/
static int32
mars4c_get_page_val(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page,uint16* p_val)
{
    if(page == MARS_PAGE_UTP)
    {
       *p_val = 0x0;
    }
    else if(page == MARS_PAGE_QSGMII)
    {
       *p_val = 0x2;
    }
    else if(page == MARS_PAGE_SGMII)
    {
       *p_val = 0x3;
    }
    else if(page == MARS_PAGE_LDS)
    {
       *p_val = 0x0;
    }
    else if(page == MARS_PAGE_FIBER_LED)
    {
       *p_val = 0x1;
    }
    else
    {
       return CTC_E_INVALID_PARAM;
    }

    return CTC_E_NONE;
}

static int32
mars4c_reg_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint8 reg, uint16* value)
{
    param->reg = reg;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param));
    PHY_DEBUG_PRINT("phy addr %d: read reg 0x%x: 0x%x\n", param->phy_addr, param->reg, param->value);

    *value = param->value;
    return CTC_E_NONE;
}

static int32
mars4c_reg_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint8 reg, uint16 value)
{
    param->reg = reg;
    param->value = value;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));
    PHY_DEBUG_PRINT("phy addr %d: write reg 0x%x: 0x%x\n", param->phy_addr, param->reg,param->value);

    return CTC_E_NONE;
}

static int32
mars4c_reg_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint8 reg, uint16 value, uint16 mask)
{
    param->reg = reg;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param));

    value = (value & mask) | (param->value & ~mask);

    param->reg = reg;
    param->value = value;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));
    PHY_DEBUG_PRINT("phy addr %d: write reg 0x%x: 0x%x\n", param->phy_addr, param->reg,param->value);

    return CTC_E_NONE;
}

static int32
mars4c_ext_reg_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16* value)
{
    param->reg = MARS_EXT_REG_ADDR;
    param->value = reg;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = MARS_EXT_REG_DATA;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param));
    PHY_DEBUG_PRINT("phy addr %d: read reg 0x%x: 0x%x\n", param->phy_addr, param->reg, param->value);

    *value = param->value;
    return CTC_E_NONE;
}

static int32
mars4c_ext_reg_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 value)
{
    param->reg = MARS_EXT_REG_ADDR;
    param->value = reg;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = MARS_EXT_REG_DATA;
    param->value = value;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));
    PHY_DEBUG_PRINT("phy addr %d: write reg 0x%x: 0x%x\n", param->phy_addr, param->reg,param->value);

    return CTC_E_NONE;
}

static int32
mars4c_ext_reg_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 value, uint16 mask)
{
    param->reg = MARS_EXT_REG_ADDR;
    param->value = reg;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = MARS_EXT_REG_DATA;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param));

    value = (value & mask) | (param->value & ~mask);
    param->reg = MARS_EXT_REG_DATA;
    param->value = value;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));
    PHY_DEBUG_PRINT("phy addr %d: write reg 0x%x: 0x%x\n", param->phy_addr, param->reg,param->value);

    return CTC_E_NONE;
}

static
int32 mars4c_mmd_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 mmdaddr, uint16 reg, uint16 *value)
{
    param->reg = 0xd;
    param->value = mmdaddr;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = 0xe;
    param->value = reg;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = 0xd;
    param->value = 0x4000|mmdaddr;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = 0xe;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param));

    *value = param->value;
    return CTC_E_NONE;
}

static
int32 mars4c_mmd_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 mmdaddr, uint16 reg, uint16 value, uint16 mask)
{
    param->reg = 0xd;
    param->value = mmdaddr;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = 0xe;
    param->value = reg;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = 0xd;
    param->value = 0x4000|mmdaddr;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    param->reg = 0xe;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param));
    value = (value & mask) | (param->value & ~mask);

    param->reg = 0xe;
    param->value = value;
    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param));

    return CTC_E_NONE;
}

static int32 mars4c_page_access_start(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page)
{
    uint16 value = 0;

    PHY_MARS_ERROR_RETURN(mars4c_get_page_val(lchip, param, page, &value));
    if(page == MARS_PAGE_LDS)
    {
        PHY_MARS_ERROR_RETURN(mars4c_ext_reg_write_mask(lchip, param, 0x100, 0x0, 0x2));
    }
    else if(page == MARS_PAGE_FIBER_LED)
    {
        PHY_MARS_ERROR_RETURN(mars4c_ext_reg_write_mask(lchip, param, 0xa054, value, 0x1));
        PHY_MARS_ERROR_RETURN(mars4c_ext_reg_read(lchip, param, 0xa054, &value));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(mars4c_ext_reg_write_mask(lchip, param, MARS_PAGE_REG, value, MARS_PAGE_MASK));
    }

    return CTC_E_NONE;
}

static int32 mars4c_page_access_stop(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page)
{
    if(page == MARS_PAGE_LDS)
    {
        PHY_MARS_ERROR_RETURN(mars4c_ext_reg_write_mask(lchip, param, 0x100, 0x2, 0x2));
    }
    else if(page == MARS_PAGE_FIBER_LED)
    {
        PHY_MARS_ERROR_RETURN(mars4c_ext_reg_write_mask(lchip, param, 0xa054, 0x0, 0x1));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(mars4c_ext_reg_write_mask(lchip, param, MARS_PAGE_REG, 0x0, MARS_PAGE_MASK));
    }

    return CTC_E_NONE;
}

static int32
mars4c_update_port_type(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 mode)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    if(mode == MARS4C_QSGMIIx1_FIBERx4 || mode == MARS4C_QSGMIIx1_SGMIIx4)
    {
        g_phy_port_info[port_id].port_type = MARS_PORT_TYPE_FIBER;
    }
    else
    {
        g_phy_port_info[port_id].port_type = MARS_PORT_TYPE_COPPER;
    }

    return CTC_E_NONE;
}

static int32
mars4c_update_port_medium(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 mode)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    if(mode == MARS4C_QSGMIIx1_COPPERx4)
    {
        g_phy_port_info[port_id].mdium = GLB_MEDIA_RJ45;
    }
    else if(mode == MARS4C_QSGMIIx1_FIBERx4)
    {
        g_phy_port_info[port_id].mdium = GLB_MEDIA_1000BX;
    }
    else if(mode == MARS4C_QSGMIIx1_COMBOx4)
    {
        g_phy_port_info[port_id].mdium = GLB_MEDIA_AMS_CU_1000BX;
    }
    else if(mode == MARS4C_QSGMIIx1_SGMIIx4)
    {
        g_phy_port_info[port_id].mdium = GLB_MEDIA_1000BX;
    }
    else if(mode == MARS4C_SGMIIx4_COPPERx4)
    {
        g_phy_port_info[port_id].mdium = GLB_MEDIA_RJ45;
    }

    return CTC_E_NONE;
}

int32 ctc_phy_mars4c_ext_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 *value)
{
    uint8 port_id = 0;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_ext_reg_read(lchip,param,reg,value));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32 ctc_phy_mars4c_ext_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 value)
{
    uint8 port_id = 0;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_ext_reg_write(lchip,param,reg,value));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_ext_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 value, uint16 mask)
{
    uint8 port_id = 0;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_ext_reg_write_mask(lchip,param, reg,value,mask));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_page_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page, uint16 reg, uint16* value)
{
    uint8 port_id = 0;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_start(lchip,param,page));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_reg_read(lchip,param,reg,value));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_stop(lchip,param,page));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_page_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page, uint16 reg, uint16 value)
{
    uint8 port_id = 0;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_start(lchip,param,page));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_reg_write(lchip,param,reg,value));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_stop(lchip,param,page));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_page_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page, uint16 reg, uint16 value, uint16 mask)
{
    uint8 port_id = 0;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_start(lchip,param,page));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_reg_write_mask(lchip, param, reg, value, mask));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_stop(lchip,param,page));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_page_ext_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page, uint16 reg, uint16* value)
{
    uint8 port_id = 0;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_start(lchip,param,page));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_ext_reg_read(lchip,param,reg,value));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_stop(lchip,param,page));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_page_ext_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page, uint16 reg, uint16 value)
{
    uint8 port_id = 0;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_start(lchip,param,page));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_ext_reg_write(lchip,param,reg,value));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_stop(lchip,param,page));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_page_ext_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 page, uint16 reg, uint16 value, uint16 mask)
{
    uint8 port_id = 0;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_start(lchip,param,page));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_ext_reg_write_mask(lchip,param,reg,value,mask));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_stop(lchip,param,page));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_mmd_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 mmdaddr, uint16 reg, uint16* value)
{
    uint8 port_id = 0;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_start(lchip,param,MARS_PAGE_UTP));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_mmd_read(lchip, param, mmdaddr, reg, value));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_stop(lchip,param,MARS_PAGE_UTP));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_mmd_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 mmdaddr, uint16 reg, uint16 value, uint16 mask)
{
    uint8 port_id = 0;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_SEM_TAKE;

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_start(lchip,param,MARS_PAGE_UTP));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_mmd_write_mask(lchip, param, mmdaddr, reg, value, mask));

    PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(mars4c_page_access_stop(lchip,param,MARS_PAGE_UTP));

    PHY_MARS_SEM_GIVE;

    return CTC_E_NONE;
}

static int32
mars4c_get_link_up_medium_type(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    uint8 linkupu = 0;
    uint8 linkups = 0;
    uint16 valu = 0;
    uint16 vals = 0;
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip,param, MARS_PAGE_UTP, 0x11, &valu));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip,param, MARS_PAGE_SGMII, 0x11, &vals));
    linkupu = (valu & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;
    linkups = (vals & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;

    if(linkupu == GLB_LINK_UP)
    {
        g_phy_port_info[port_id].mdium_status = GLB_MEDIA_RJ45;
    }
    else if(linkups == GLB_LINK_UP)
    {
        if(g_phy_port_info[port_id].speed_status == CTC_PORT_SPEED_1G)
        {
            g_phy_port_info[port_id].mdium_status = GLB_MEDIA_1000BX;
        }
        else if(g_phy_port_info[port_id].speed_status == CTC_PORT_SPEED_100M)
        {
            g_phy_port_info[port_id].mdium_status = GLB_MEDIA_FI_100FX;
        }
    }

    return CTC_E_NONE;
}

static int32 mars4c_phy_conf_set(uint8 lchip, ctc_chip_mdio_para_t* param,uint8 speed, uint8 duplex)
{
    uint16 reg4=0, reg9=0,reg0_mask=0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);

    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_COPPER)
    {
        /* config Auto-Negotiation Advertisement */
        switch(speed)
        {
            case GLB_SPEED_1G:
                if(duplex == GLB_DUPLEX_FULL)
                {
                    reg4 = 0x1c01;
                    reg9 = 0x200;
                }
                else if(duplex == GLB_DUPLEX_HALF)
                {
                    reg4 = 0x1c01;
                    reg9 = 0x100;
                }
                else
                {
                    reg4 = 0x1c01;
                    reg9 = 0x300;
                }
                break;
            case GLB_SPEED_100M:
                if(duplex == GLB_DUPLEX_FULL)
                {
                    reg4 = 0x1d01;
                    reg9 = 0;
                }
                else if(duplex == GLB_DUPLEX_HALF)
                {
                    reg4 = 0x1c81;
                    reg9 = 0;
                }
                else
                {
                    reg4 = 0x1d81;
                    reg9 = 0;
                }
                break;
            case GLB_SPEED_10M:
                if(duplex == GLB_DUPLEX_FULL)
                {
                    reg4 = 0x1c41;
                    reg9 = 0;
                }
                else if(duplex == GLB_DUPLEX_HALF)
                {
                    reg4 = 0x1c21;
                    reg9 = 0;
                }
                else
                {
                    reg4 = 0x1c61;
                    reg9 = 0;
                }
                break;
            default:
                if(duplex == GLB_DUPLEX_FULL)
                {
                    reg4 = 0x1d41;
                    reg9 = 0x200;
                }
                else if(duplex == GLB_DUPLEX_HALF)
                {
                    reg4 = 0x1ca1;
                    reg9 = 0x100;
                }
                else
                {
                    reg4 = 0x1de1;
                    reg9 = 0x300;
                }
                break;
        }
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_AN_ADVERTI_REG, reg4, 0x1de1));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_1G_BASET_CTL_REG, reg9, 0x300));

        reg0_mask = 0x2140;
        if (g_phy_port_info[port_id].auto_neg_en == 0) /* Force mode*/
        {
            reg0_mask = 0x3140;/* mask for Auto-Negotiation */
        }
        /* config manual speed with Auto-Negotiation mask */
        if((speed == GLB_SPEED_10M)&&((duplex == GLB_DUPLEX_FULL)||(duplex == GLB_DUPLEX_MAX)))
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0100, reg0_mask));
        }
        else if((speed == GLB_SPEED_10M)&&(duplex == GLB_DUPLEX_HALF))
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0000, reg0_mask));
        }
        else if((speed == GLB_SPEED_100M)&&((duplex == GLB_DUPLEX_FULL)||(duplex == GLB_DUPLEX_MAX)))
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x2100, reg0_mask));
        }
        else if((speed == GLB_SPEED_100M)&&(duplex == GLB_DUPLEX_HALF))
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x2000, reg0_mask));
        }
        else if((speed == GLB_SPEED_1G)&&((duplex == GLB_DUPLEX_FULL)||(duplex == GLB_DUPLEX_MAX)))
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0140, reg0_mask));
        }
        else if((speed == GLB_SPEED_1G)&&(duplex == GLB_DUPLEX_HALF))
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0040, reg0_mask));
        }
        else /* default speed 1G duplex full */
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0140, reg0_mask));
        }

        if (g_phy_port_info[port_id].auto_neg_en == 0) /* Force mode*/
        {
            /*When config force mode, need to powerdown and powerup port to notify link parter.*/
            if(g_phy_port_info[port_id].enable)
            {
                PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0800, 0x0800));
                if(speed == GLB_SPEED_10M)
                {
                    sal_udelay(1000000);
                }
                else
                {
                    sal_udelay(200000);
                }
                PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0000, 0x0800));
            }
        }
        else
        {
            /* restart Auto-Negotiation */
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x1200, 0x1200));
        }
    }
    else
    {
        /* config fiber/sgmii speed */
        if(speed == GLB_SPEED_1G)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip,param, MARS_PAGE_SGMII, 0xa5, 0x0000, 0x8000));
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa009, 0x1 << (phyaddr - baseaddr), 0x1 << (phyaddr - baseaddr)));
        }
        else if(speed == GLB_SPEED_100M)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip,param, MARS_PAGE_SGMII, 0xa5, 0x0000, 0x8000));
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa009, 0x0, 0x1 << (phyaddr - baseaddr)));
        }
        else
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip,param, MARS_PAGE_SGMII, 0xa5, 0x8000, 0x8000));
        }
    }

    return CTC_E_NONE;
}

static uint16
mars4c_get_lds_result(uint8 lchip, ctc_chip_mdio_para_t* param,uint16* p_result)
{
    uint16 value = 0;
    uint16 result = 0;
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_LDS, 0xb, &value));
    if(value & 0x1)
    {
        result = MARS_LDS_RESULT_2_PAIR_10M;
    }
    else if(value & 0x2)
    {
        result = MARS_LDS_RESULT_2_PAIR_100M;
    }
    else if(value & 0x4)
    {
        result = MARS_LDS_RESULT_1_PAIR_10M;
    }
    else if(value & 0x8)
    {
        result = MARS_LDS_RESULT_1_PAIR_100M;
    }
    else if(value & 0x20)
    {
        result = MARS_LDS_RESULT_4_PAIR_100M;
    }
    else
    {
        result = MARS_LDS_RESULT_DEFAULT;
    }
    g_phy_port_info[port_id].lds_result = result;
    *p_result = result;

    return CTC_E_NONE;
}

static int32
mars4c_init_medium(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    uint16 val = 0;
    uint16 mode = 0;
    uint8 port_id = 0;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param, 0xa007, &val));
    if((val & 0x7) == 0x2)
    {
        mode = MARS4C_QSGMIIx1_COPPERx4;
        g_phy_port_info[port_id].mdium = GLB_MEDIA_RJ45;
    }
    else if((val & 0x7) == 0x3)
    {
        mode = MARS4C_QSGMIIx1_FIBERx4;
        g_phy_port_info[port_id].mdium = GLB_MEDIA_1000BX;
    }
    else if((val & 0x7) == 0x4)
    {
        mode = MARS4C_QSGMIIx1_COMBOx4;
        g_phy_port_info[port_id].mdium = GLB_MEDIA_AMS_CU_1000BX;
    }
    else if((val & 0x7) == 0x5)
    {
        mode = MARS4C_QSGMIIx1_COMBOx4;
        g_phy_port_info[port_id].mdium = GLB_MEDIA_AMS_CU_1000BX;
    }
    else if((val & 0x7) == 0x6)
    {
        mode = MARS4C_QSGMIIx1_SGMIIx4;
        g_phy_port_info[port_id].mdium = GLB_MEDIA_1000BX;
    }
    else if((val & 0x7) == 0x7)
    {
        mode = MARS4C_SGMIIx4_COPPERx4;
        g_phy_port_info[port_id].mdium = GLB_MEDIA_RJ45;
    }
    PHY_MARS_ERROR_RETURN(mars4c_update_port_type(lchip, param, mode));

    return CTC_E_NONE;
}

static uint16
mars4c_set_patch(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    uint16 addr = 0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);
    addr = phyaddr - baseaddr;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_UTP, 0x41, 0x33));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_UTP, 0x42, 0x66));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_UTP, 0x43, 0xaa));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_UTP, 0x44, 0xd0d));
    if (addr == 0x2 || addr == 0x5)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_UTP, 0x57, 0x2929));
    }
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x0, 0x9140));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_init(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    uint16 val = 0;
    uint8 port_id;

    PHY_MARS_ERROR_RETURN(ctc_phy_mdio_init());

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ctc_phy_common_probe_id(lchip,param,&g_phy_port_info[port_id].phy_id);
    g_phy_port_info[port_id].lchip = lchip;/* init */
    g_phy_port_info[port_id].bus = param->bus;
    g_phy_port_info[port_id].phy_addr = param->phy_addr;
    g_phy_port_info[port_id].ctl_id = param->ctl_id;
    g_phy_port_info[port_id].dev_no = param->dev_no;
    g_phy_port_info[port_id].mac_if = GLB_MAC_INTERFACE_QSGMII;/* init */
    g_phy_port_info[port_id].mdium = GLB_MEDIA_RJ45;/* init */
    g_phy_port_info[port_id].duplex = GLB_DUPLEX_MAX;/* init */
    g_phy_port_info[port_id].speed = phy_speed_glb2ctc(GLB_SPEED_MAX);/* init */
    g_phy_port_info[port_id].auto_neg_en = 1;/* init */
    g_phy_port_info[port_id].enable = 1;/* init */
    g_phy_port_info[port_id].auto_neg_status = g_phy_port_info[port_id].auto_neg_en;/* init */
    g_phy_port_info[port_id].enable_status = g_phy_port_info[port_id].enable;/* init */
    g_phy_port_info[port_id].duplex_status = GLB_DUPLEX_FULL;/* init */
    g_phy_port_info[port_id].speed_status = CTC_PORT_SPEED_1G;/* init */
    g_phy_port_info[port_id].mdium_status = g_phy_port_info[port_id].mdium;/* init */
    g_phy_port_info[port_id].loopback_status = g_phy_port_info[port_id].loopback_mode;/* init */
    g_phy_port_info[port_id].undir_status = g_phy_port_info[port_id].undir_en;/* init */
    g_phy_port_info[port_id].port_type = MARS_PORT_TYPE_COPPER;/* init */
    g_phy_port_info[port_id].sem_take = NULL;/* init */
    g_phy_port_info[port_id].sem_give = NULL;/* init */

    /* do phy hardware reset per-chip before do phy port init */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param, 0xa0ff, &val));
    if (val == 0x5555)
    {
        PHY_DEBUG_PRINT("port %d hardware reset!\n",port_id);
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param, 0xa0c0, 0x8000, 0x8000));
        sal_udelay(50000);
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write(lchip, param, 0xa0ff, 0xaaaa));
    }

    /* config chip mode */
    PHY_MARS_ERROR_RETURN(mars4c_init_medium(lchip, param));

    /* enable fast link */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x34, 0x000, 0x8000));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x37, 0xe000, 0xe000));

    /* enable interrupt */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write(lchip, param,0xa010,0xffff));
    /* clear interrupt status */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param,0xa011,&val));

    /* keep ext_reg to 0x0000 */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write(lchip, param,0xa000,0));

    /* enable interrupt */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x12, 0x6c00));
    /* clear interrupt status */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_UTP, 0x13, &val));

    /* led mode config */
    //PHY_MARS_ERROR_RETURN(mars4c_port_led_config(0,param));

    /* keep ext_reg to 0x0000 */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write(lchip, param,0xa000,0));

    /* set 4c patch */
    PHY_MARS_ERROR_RETURN(mars4c_set_patch(lchip, param));

    /* do phy software reset when do phy port init */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x8000, 0x8000));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_deinit(uint8 lchip, ctc_chip_mdio_para_t* param)
{

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_port_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    uint8 port_id;
    uint16 page;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_COPPER)
    {
        page = MARS_PAGE_UTP;
    }
    else
    {
        page = MARS_PAGE_SGMII;
    }

    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, page, PHY_CTL_REG, 0x0000, 0x0800));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, page, PHY_CTL_REG, 0x0800, 0x0800));
    }

    g_phy_port_info[port_id].enable = enable;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_port_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint16 val = 0;
    uint16 page;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
    {
        page = MARS_PAGE_SGMII;
    }
    else
    {
        page = MARS_PAGE_UTP;
    }
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, page, PHY_CTL_REG, &val));

    *p_enable =((val>>11)&0x1)?0:1;
    g_phy_port_info[port_id].enable_status = *p_enable;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_port_duplex_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 duplex)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_COPPER)
    {
        PHY_MARS_ERROR_RETURN(mars4c_phy_conf_set(lchip, param, phy_speed_ctc2glb(g_phy_port_info[port_id].speed), duplex));
    }
    else
    {
        return ctc_phy_common_unsupport();
    }

    g_phy_port_info[port_id].duplex = duplex;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_port_duplex_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_duplex)
{
    uint16 val;
    uint16 page;
    uint32 duplex;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
    {
        page = MARS_PAGE_SGMII;
    }
    else
    {
        page = MARS_PAGE_UTP;
    }

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, page, 0x11, &val));

    duplex = (val & 0x2000) ? GLB_DUPLEX_FULL : GLB_DUPLEX_HALF;
    *p_duplex = duplex;
    g_phy_port_info[port_id].duplex_status = duplex;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_port_speed(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 value)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    PHY_MARS_ERROR_RETURN(mars4c_phy_conf_set(lchip, param, phy_speed_ctc2glb(value), g_phy_port_info[port_id].duplex));

    g_phy_port_info[port_id].speed = value;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_port_speed(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_value)
{
    uint32 speed = CTC_PORT_SPEED_MAX;
    uint16 page = 0;
    uint16 result = 0;
    uint16 value = 0;
    uint8 port_id = 0;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    PHY_MARS_ERROR_RETURN(mars4c_get_lds_result(lchip,param,&result));
    if(result == MARS_LDS_RESULT_2_PAIR_10M || result == MARS_LDS_RESULT_1_PAIR_10M)
    {
        page = MARS_PAGE_UTP;
    }
    else
    {
        page = MARS_PAGE_SGMII;
    }

    if(g_phy_port_info[port_id].lds_result)
    {
        if(g_phy_port_info[port_id].lds_result & 0x5)
        {
            speed = CTC_PORT_SPEED_10M;
        }
        else
        {
            speed = CTC_PORT_SPEED_100M;
        }
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, page, 0x11, &value));

        if(value & 0x8000)
        {
            speed = CTC_PORT_SPEED_1G;
        }
        else if(value &0x4000)
        {
            speed = CTC_PORT_SPEED_100M;
        }
        else
        {
            speed = CTC_PORT_SPEED_10M;
        }
    }

    *p_value = speed;

    g_phy_port_info[port_id].speed_status = speed;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_port_auto_neg_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    uint8 port_id;
    uint16 page;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
    {
        page = MARS_PAGE_SGMII;
    }
    else
    {
        page = MARS_PAGE_UTP;
    }

    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, page, PHY_CTL_REG, 0x1000, 0x1000));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, page, PHY_CTL_REG, 0x0000, 0x1000));
    }

    g_phy_port_info[port_id].auto_neg_en = enable;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_port_auto_neg_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint8 port_id;
    uint16 page;
    uint16 val;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
    {
        page = MARS_PAGE_SGMII;
    }
    else
    {
        page = MARS_PAGE_UTP;
    }
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, page, PHY_CTL_REG, &val));

    *p_enable = (val >> 12) & 0x1;
    g_phy_port_info[port_id].auto_neg_status = *p_enable;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_link_up_status(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_link_up)
{
    uint16 val;
    uint8 linkup;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    /* read copper status */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_UTP, 0x11, &val));
    linkup = (val & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;

    /*if link down, need read again.*/
    if(linkup == GLB_LINK_DOWN)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_UTP, 0x11, &val));
        linkup = (val & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;
    }

    if(linkup == GLB_LINK_DOWN)
    {
        /* read fiber status */
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_SGMII, 0x11, &val));
        linkup = (val & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;

        /*if link down, need read again.*/
        if(linkup == GLB_LINK_DOWN)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_SGMII, 0x11, &val));
            linkup = (val & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;
        }
    }

    *p_link_up = linkup;
    g_phy_port_info[port_id].link_up= linkup;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_page_link_status(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 page, uint32* p_link_up, uint32* p_speed)
{
    uint32 speed = CTC_PORT_SPEED_MAX;
    uint16 val;
    uint8 linkup;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, page, 0x11, &val));
    linkup = (val & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;

    /*if link down, need read again.*/
    if(linkup == GLB_LINK_DOWN)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, page, 0x11, &val));
        linkup = (val & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;
    }

    if(val & 0x8000)
    {
        speed = CTC_PORT_SPEED_1G;
    }
    else if(val & 0x4000)
    {
        val = CTC_PORT_SPEED_100M;
    }
    else if((val & 0xc000) == 0x0)
    {
        val = CTC_PORT_SPEED_10M;
    }
    else
    {
        val = CTC_PORT_SPEED_MAX;
    }

    *p_link_up = linkup;
    *p_speed = speed;

    return CTC_E_NONE;
}

static int32
mars4c_config_recover(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_port_en(lchip, param,g_phy_port_info[port_id].enable));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_port_auto_neg_en(lchip, param,g_phy_port_info[port_id].auto_neg_en));
    PHY_MARS_ERROR_RETURN(mars4c_phy_conf_set(lchip, param, phy_speed_ctc2glb(g_phy_port_info[port_id].speed), g_phy_port_info[port_id].duplex));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_linkup_event(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* user_data)
{
    uint16 val = 0;
    uint32 speed = CTC_PORT_SPEED_MAX;
    uint16 result = 0;

    /* clear interrupt status */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param,0xa011,&val));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_UTP, 0x13, &val));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_port_speed(lchip,param,&speed));
    PHY_MARS_ERROR_RETURN(mars4c_get_link_up_medium_type(lchip,param));
    PHY_MARS_ERROR_RETURN(mars4c_get_lds_result(lchip,param,&result));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_linkdown_event(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* user_data)
{
    uint16 val = 0;
    /* clear interrupt status */
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param,0xa011,&val));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_UTP, 0x13, &val));

    return CTC_E_NONE;
}

static int32 mars4c_config_loopback(uint8 lchip, ctc_chip_mdio_para_t* param, uint8 lb_mode)
{
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);

    switch (lb_mode)
    {
    case GLB_LB_NONE:
        if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_COPPER)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0000, 0x4000)); /* disable internal loopback */
            PHY_MARS_ERROR_RETURN(mars4c_config_recover(lchip,param));
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip,param, MARS_PAGE_UTP,0xa,0x00,0x20)); /* disable external loopback */
        }
        else
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_SGMII, 0x0, 0x0000, 0x4000)); /* disable sgmii internal loopback */
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param, 0xa009, 0x0, 0x1 << ((phyaddr - baseaddr) + 8))); /* disable sgmii external loopback */
        }

        break;

    case GLB_LB_PHY_FAR:/* external loopback */
        if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_COPPER)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x0000, 0x4000)); /* disable internal loopback */
            PHY_MARS_ERROR_RETURN(mars4c_config_recover(lchip,param));
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip,param, MARS_PAGE_UTP,0xa,0x20,0x20)); /* enable external loopback */
        }
        else
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_SGMII, 0x0, 0x0000, 0x4000)); /* disable sgmii internal loopback */
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param, 0xa009, 0x1 << ((phyaddr - baseaddr) + 8), 0x1 << ((phyaddr - baseaddr) + 8))); /* enable sgmii external loopback */
        }

        break;

    case GLB_LB_PHY_NEAR: /* internal loopback */
         if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_COPPER)
        {
           if (g_phy_port_info[port_id].speed == CTC_PORT_SPEED_1G)
            {
                PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x4140, 0x7140)); /* force speed and enable internal loopback */
            }
            else if (g_phy_port_info[port_id].speed == CTC_PORT_SPEED_100M)
            {
                PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x6100, 0x7140)); /* force speed and enable internal loopback */
            }
            else if (g_phy_port_info[port_id].speed == CTC_PORT_SPEED_10M)
            {
                PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x4100, 0x7140)); /* force speed and enable internal loopback */
            }
            else /* default speed 1G */
            {
                PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x4140, 0x7140)); /* force speed and enable internal loopback */
            }
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip,param, MARS_PAGE_UTP,0xa,0x00,0x20)); /* disable external loopback */
        }
        else
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param, 0xa009, 0x0, 0x1 << ((phyaddr - baseaddr) + 8))); /* disable sgmii external loopback */
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_SGMII, 0x0, 0x4000, 0x4000)); /* enable sgmii internal loopback */
        }

        break;

    default:
        return RESULT_ERROR;
        break;
    }

    return RESULT_OK;
}

int32
ctc_phy_mars4c_set_port_loopback(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 mode)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    PHY_MARS_ERROR_RETURN(mars4c_config_loopback(lchip, param,mode));

    g_phy_port_info[port_id].loopback_mode = mode;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_port_loopback(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* mode)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    *mode = g_phy_port_info[port_id].loopback_mode;
    return RESULT_OK;
}

int32
ctc_phy_mars4c_set_port_unidir_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
    {
        if(enable)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_SGMII, 0x0, 0x0000, 0x1000));
            if(g_phy_port_info[port_id].speed == CTC_PORT_SPEED_1G)
            {
                PHY_MARS_ERROR_RETURN(mars4c_phy_conf_set(lchip, param, phy_speed_ctc2glb(CTC_PORT_SPEED_1G)\
					, g_phy_port_info[port_id].duplex));
            }
            else if(g_phy_port_info[port_id].speed == CTC_PORT_SPEED_100M)
            {
                PHY_MARS_ERROR_RETURN(mars4c_phy_conf_set(lchip, param, phy_speed_ctc2glb(CTC_PORT_SPEED_100M)\
					, g_phy_port_info[port_id].duplex));
            }
            else
            {
                PHY_MARS_ERROR_RETURN(mars4c_phy_conf_set(lchip, param, phy_speed_ctc2glb(CTC_PORT_SPEED_1G)\
					, g_phy_port_info[port_id].duplex));
            }
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_SGMII, 0x0, 0x0020, 0x0020));
        }
        else
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_SGMII, 0x0, 0x0000, 0x0020));
            PHY_MARS_ERROR_RETURN(mars4c_config_recover(lchip, param));
        }
    }
    else
    {
        return ctc_phy_common_unsupport();
    }

    g_phy_port_info[port_id].undir_en = enable;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_port_unidir_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* enable)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    *enable = g_phy_port_info[port_id].undir_en;
    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_fiber_to_sgmii_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);

    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa019, 0x1 << (phyaddr - baseaddr), 0x1 << (phyaddr - baseaddr)));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa019, 0x0, 0x1 << (phyaddr - baseaddr)));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_fiber_to_sgmii_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* enable)
{
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    uint16 val = 0;

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param, 0xa019, &val));
    if(val & (0x1 << (phyaddr - baseaddr)))
    {
        *enable = GLB_ENABLE;
    }
    else
    {
        *enable = GLB_DISABLE;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_chip_mode(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 mode)
{
    uint16 val = 0;

    switch (mode)
    {
        case MARS4C_QSGMIIx1_COPPERx4:
            val = 2;
            break;
        case MARS4C_QSGMIIx1_FIBERx4:
            val = 3;
            break;
        case MARS4C_QSGMIIx1_COMBOx4:
            val = 4;
            break;
        case MARS4C_QSGMIIx1_SGMIIx4:
            val = 6;
            break;
        case MARS4C_SGMIIx4_COPPERx4:
            val = 7;
            break;
        default:
            return CTC_E_INVALID_PARAM;
    }

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa007, val, 0x0007));
    PHY_MARS_ERROR_RETURN(mars4c_update_port_medium(lchip, param, mode));
    PHY_MARS_ERROR_RETURN(mars4c_update_port_type(lchip, param, mode));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_chip_mode(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* mode)
{
    uint16 val = 0;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param, 0xa007, &val));
    val &= 0x7;

    switch (val)
    {
        case 2:
            *mode = MARS4C_QSGMIIx1_COPPERx4;
            break;
        case 3:
            *mode = MARS4C_QSGMIIx1_FIBERx4;
            break;
        case 4:
            *mode = MARS4C_QSGMIIx1_COMBOx4;
            break;
        case 5:
            *mode = MARS4C_QSGMIIx1_COMBOx4;
            break;
        case 6:
            *mode = MARS4C_QSGMIIx1_SGMIIx4;
            break;
        case 7:
            *mode = MARS4C_SGMIIx4_COPPERx4;
            break;
        default:
            return CTC_E_INVALID_PARAM;
    }

    return RESULT_OK;
}

int32
ctc_phy_mars4c_set_port_medium(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type)
{
    uint16 val = 0;
    uint16 mode = 0;
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    switch (type)
    {
        case GLB_MEDIA_RJ45:
            val = 2;
            mode = MARS4C_QSGMIIx1_COPPERx4;
            break;
        case GLB_MEDIA_1000BX:
            val = 3;
            mode = MARS4C_QSGMIIx1_FIBERx4;
            break;
        case GLB_MEDIA_AMS_CU_1000BX:
            val = 4;
            mode = MARS4C_QSGMIIx1_COMBOx4;
            break;
        default:
            return CTC_E_INVALID_PARAM;
    }

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa007, val, 0x0007));
    PHY_MARS_ERROR_RETURN(mars4c_update_port_type(lchip, param, mode));
    g_phy_port_info[port_id].mdium = type;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_port_medium(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* type)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    *type = g_phy_port_info[port_id].mdium;
    return RESULT_OK;
}

int32
ctc_phy_mars4c_set_packet_checker(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable, uint32 side)
{
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    uint16 regaddr = 0;
    uint16 val = 0;

    regaddr = 0xa0b7;
    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);
    regaddr |= (phyaddr - baseaddr) << 8;

    if(side == MARS_PACKET_CHECKER_UPSTREAM)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0xc000,0xc000));
    }
    else if(side == MARS_PACKET_CHECKER_DOWNSTREAM)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x0000,0xc000));
    }
    else
    {
        return ctc_phy_common_unsupport();
    }

    regaddr = 0xa0a0;
    regaddr |= (phyaddr - baseaddr) << 8;
    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x8000,0xc000));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));
        if(val & 0x1000)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x0000,0xc000));
        }
        else
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x4000,0xc000));
        }
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_packet_checker(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable, uint32* side)
{
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    uint16 regaddr = 0;
    uint16 val = 0;

    regaddr = 0xa0a0;

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);
    regaddr |= (phyaddr - baseaddr) << 8;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));

    if((val & 0xc000) == 0x8000)
    {
        *p_enable = GLB_ENABLE;
    }
    else
    {
        *p_enable = GLB_DISABLE;
    }

    regaddr = 0xa0b7;
    regaddr |= (phyaddr - baseaddr) << 8;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));
    if((val & 0xc000) == 0xc000)
    {
        *side = MARS_PACKET_CHECKER_UPSTREAM;
    }
    else
    {
        *side = MARS_PACKET_CHECKER_DOWNSTREAM;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_packet_count(uint8 lchip, ctc_chip_mdio_para_t* param, void* p_pkt_count)
{
    uint16 regaddr = 0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    uint16 val,good_high,good_low,errorcount;
    mars_packet_generator_count_t* packet_count = NULL;

    packet_count = (mars_packet_generator_count_t*)p_pkt_count;
    regaddr = 0xa0b7;

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);
    regaddr |= (phyaddr - baseaddr) << 8;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));
    if((val & 0xc000) == 0xc000)
    {
        packet_count->side= MARS_PACKET_CHECKER_UPSTREAM;
    }
    else if((val & 0xc000) == 0x0000)
    {
        packet_count->side= MARS_PACKET_CHECKER_DOWNSTREAM;
    }
    else
    {
        packet_count->side= MARS_PACKET_CHECKER_STREAM_MAX;
    }

    regaddr = 0xa0a3;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&good_high));
    regaddr = 0xa0a4;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&good_low));
    packet_count->rx_good = (good_high << 16) | good_low;

    regaddr = 0xa0a9;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&errorcount));
    packet_count->rx_error = errorcount;

    regaddr = 0xa0ad;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&good_high));
    regaddr = 0xa0ae;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&good_low));
    packet_count->tx_good = (good_high << 16) | good_low;

    regaddr = 0xa0b3;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&errorcount));
    packet_count->tx_error = errorcount;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_packet_gen(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    uint16 regaddr = 0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    mars_packet_generator_t* packet_gen;

    packet_gen = (mars_packet_generator_t*)pv_arg;
    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);

    regaddr = 0xa0a2;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,packet_gen->packet_num,0xffff));

    if((packet_gen->packet_len >= 64) && (packet_gen->packet_len <= 1512))
    {
        regaddr = 0xa0a1;
        regaddr |= (phyaddr - baseaddr) << 8;
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write(lchip,param,regaddr,packet_gen->packet_len));
    }

    regaddr = 0xa0b7;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,(packet_gen->addr_en & 0x1) << 12,0x1000));
    regaddr = 0xa0b9;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,(packet_gen->addr_sa & 0xff),0x00ff));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,((packet_gen->addr_da & 0xff) << 8),0xff00));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_packet_gen(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    uint16 val;
    uint16 regaddr = 0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    mars_packet_generator_t* packet_gen;

    packet_gen = (mars_packet_generator_t*)pv_arg;
    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);

    regaddr = 0xa0a2;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));
    packet_gen->packet_num = val;

    regaddr = 0xa0a1;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));
    packet_gen->packet_len = val;

    regaddr = 0xa0b7;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));
    if((val >> 12) & 0x1)
    {
        packet_gen->addr_en= GLB_ENABLE;
    }
    else
    {
        packet_gen->addr_en= GLB_DISABLE;
    }
    regaddr = 0xa0b9;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));
    packet_gen->addr_sa = val & 0xff;
    packet_gen->addr_da = (val >> 8) & 0xff;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_packet_gen_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    uint16 val = 0;
    uint16 regaddr = 0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);

    if(enable)
    {
        regaddr = 0xa0a0;
        regaddr |= (phyaddr - baseaddr) << 8;
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x0000,0x6000));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x1000,0x1000));
    }
    else
    {
        regaddr = 0xa0a0;
        regaddr |= (phyaddr - baseaddr) << 8;
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));
        if(val & 0x8000)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x0000,0x1000));
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x2000,0x7000));
        }
        else
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x0000,0x1000));
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip,param,regaddr,0x6000,0x7000));
        }
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_packet_gen_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint16 val;
    uint16 regaddr = 0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);

    regaddr = 0xa0a0;
    regaddr |= (phyaddr - baseaddr) << 8;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,regaddr,&val));

    if((val >> 12) & 0x1)
    {
        *p_enable = GLB_ENABLE;
    }
    else
    {
        *p_enable = GLB_DISABLE;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_sleep_mode_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x27, 0x8000, 0x8000));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x27, 0x0000, 0x8000));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_sleep_mode_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint16 val;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x27,&val));

    *p_enable = (val & 0x8000) ? GLB_ENABLE : GLB_DISABLE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_eee_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_mmd_write_mask(lchip, param, 0x7, 0x3c, 0x6, 0x6));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x0, 0x8000, 0x8000));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x9a, 0x0000, 0x8000));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_mmd_write_mask(lchip, param, 0x7, 0x3c, 0x0, 0x6));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x0, 0x8000, 0x8000));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x9a, 0x8000, 0x8000));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_eee_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint16 val;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_mmd_read(lchip, param, 0x7, 0x3c, &val));

    *p_enable = (val & 0x6) ? GLB_ENABLE : GLB_DISABLE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_eee_status(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_status)
{
    uint16 val;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_mmd_read(lchip, param, 0x3, 0x1, &val));

    *p_status = ((val & 0x300) == 0x300) ? MARS_EEE : MARS_OUT_EEE;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_vct_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_UTP, 0x98, 0xb0a6));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_sleep_mode_en(lchip, param, GLB_DISABLE));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x80, 0x1,0x1));
    }

    return CTC_E_NONE;
}

int32
mars4c_vct_status_prase(uint16 vct_status)
{
    if(vct_status == 0x0)
    {
        return MARS_PAIR_STATE_NORMAL;
    }
    else if(vct_status == 0x1)
    {
        return MARS_PAIR_STATE_ABNORMAL_TERMINATION;
    }
    else if(vct_status == 0x2)
    {
        return MARS_PAIR_STATE_ABNORMAL_SHORTED;
    }
    else if(vct_status == 0x3)
    {
        return MARS_PAIR_STATE_ABNORMAL_OPEN;
    }
    else
    {
        return MARS_PAIR_STATE_MAX;
    }
}

int32
ctc_phy_mars4c_get_vct_result(uint8 lchip, ctc_chip_mdio_para_t* param, void* result)
{
    mars_port_cable_info_t* p_cable_info;
    uint16 val = 0;
    uint16 A_status,B_status,C_status,D_status;

    p_cable_info = (mars_port_cable_info_t*)result;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x84, &val));
    if((val&0x8000)==0)
    {
        A_status = val & 0x3;
        B_status = (val>>2) & 0x3;
        C_status = (val>>4) & 0x3;
        D_status = (val>>6) & 0x3;
        p_cable_info->pair_A.pair_status = mars4c_vct_status_prase(A_status);
        p_cable_info->pair_B.pair_status = mars4c_vct_status_prase(B_status);
        p_cable_info->pair_C.pair_status = mars4c_vct_status_prase(C_status);
        p_cable_info->pair_D.pair_status = mars4c_vct_status_prase(D_status);

        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x87, &val));
        p_cable_info->pair_A.pair_length = (val/100) ? (val/100) : 1;;
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x88, &val));
        p_cable_info->pair_B.pair_length = (val/100) ? (val/100) : 1;
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x89, &val));
        p_cable_info->pair_C.pair_length = (val/100) ? (val/100) : 1;
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x8a, &val));
        p_cable_info->pair_D.pair_length = (val/100) ? (val/100) : 1;
    }
    else
    {
        return CTC_E_NOT_READY;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_lds_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_LDS, 0x0, enable << 12,0x1000));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_LDS, 0x0, 0x8000,0x8000));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_lds_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint16 val = 0;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_LDS, 0x0, &val));
    *p_enable = (val >> 12) & 0x1;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_lds_details(uint8 lchip, ctc_chip_mdio_para_t* param, void* p_result)
{
    mars_lds_details_t* lds_details;
    uint16 val1 = 0;
    uint16 vala = 0;
    uint16 result = 0;

    lds_details = (mars_lds_details_t*)p_result;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_LDS, 0x1, &val1));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_LDS, 0xa, &vala));

    lds_details->linkup= (val1 >> 2) & 0x1;
    lds_details->length= vala & 0xfff;
    PHY_MARS_ERROR_RETURN(mars4c_get_lds_result(lchip, param,&result));
    lds_details->result= result;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_link_status_details(uint8 lchip, ctc_chip_mdio_para_t* param, void* p_link_status)
{
    mars_link_status_t* link_status;

    link_status = (mars_link_status_t*)p_link_status;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_port_speed(lchip,param,&link_status->speed_status));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_port_duplex_en(lchip,param,&link_status->duplex_status));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_port_auto_neg_en(lchip,param,&link_status->auto_neg_en));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_link_up_status(lchip,param,&link_status->link_up));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_page_link_status(lchip,param, MARS_PAGE_QSGMII,&link_status->qsg_link_up,&link_status->qsg_speed_status));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_page_link_status(lchip,param, MARS_PAGE_SGMII,&link_status->sg_link_up,&link_status->sg_speed_status));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_mdi_mdix_mode(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 mode)
{
    if(mode == MARS_MANUAL_MDI)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x10, 0x0, 0x0060));
    }
    else if(mode == MARS_MANUAL_MDIX)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x10, 0x20, 0x0060));
    }
    else if(mode == MARS_MDI_MDIX_AUTO)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x10, 0x60, 0x0060));
    }
    else
    {
        return ctc_phy_common_unsupport();
    }

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x0, 0x8000, 0x8000));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_mdi_mdix_mode(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_mode)
{
    uint16 val;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_UTP, 0x10, &val));
    if((val & 0x60) == 0x0)
    {
        *p_mode = MARS_MANUAL_MDI;
    }
    else if((val & 0x60) == 0x20)
    {
        *p_mode = MARS_MANUAL_MDIX;
    }
    else if((val & 0x60) == 0x60)
    {
        *p_mode = MARS_MDI_MDIX_AUTO;
    }
    else
    {
        return CTC_E_UNEXPECT;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_downgrade_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x14, 0x0020, 0x0020));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, PHY_CTL_REG, 0x8000, 0x8000));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x14, 0x0000, 0x0020));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, PHY_CTL_REG, 0x8000, 0x8000));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_downgrade_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint16 val;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip, param, MARS_PAGE_UTP, 0x14, &val));
    if(val & 0x20)
    {
        *p_enable = GLB_ENABLE;
    }
    else
    {
        *p_enable = GLB_DISABLE;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_fast_link_down(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable, uint32 delay)
{
    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x34, 0x8000, 0x8000));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x37, (delay & 0x7) << 13, 0xe000));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x34, 0x0000, 0x8000));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x37, (delay & 0x7) << 13, 0xe000));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_fast_link_down(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable, uint32* p_delay)
{
    uint16 val;
    uint16 delay;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x34, &val));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x37, &delay));
    if(val & 0x8000)
    {
        *p_enable = GLB_ENABLE;
    }
    else
    {
        *p_enable = GLB_DISABLE;
    }
    *p_delay = delay >> 13;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_led_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa004, 0x0000, 0x0100));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa004, 0x0100, 0x0100));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_led_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint16 val = 0;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param,0xa004, &val));
    if(((val >> 8) & 0x1))
    {
        *p_enable = GLB_DISABLE;
    }
    else
    {
        *p_enable = GLB_ENABLE;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_led_mode(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 mode)
{
    if(mode == MARS_LED_MODE0)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa004, 0x0000, 0x0030));
    }
    else if(mode == MARS_LED_MODE1)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa004, 0x0010, 0x0030));
    }
    else if(mode == MARS_LED_MODE2)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa004, 0x0020, 0x0030));
    }
    else if(mode == MARS_LED_MODE3)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa004, 0x0030, 0x0030));
    }
    else
    {
        return ctc_phy_common_unsupport();
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_led_mode(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_mode)
{
    uint16 val = 0;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param,0xa004, &val));
    *p_mode = (val >> 4) & 0x3;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_led_glb_config(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    int16 val = 0;
    mars_led_details_t* led_details;

    led_details = (mars_led_details_t*)pv_arg;
    val = ((led_details->act_low & 0x1) << 11) | ((led_details->bit_mask & 0x7) << 8)
		| (led_details->port_en_ctrl & 0xff);
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa001, val, 0x0fff));

    val = ((led_details->clk_en & 0x1) << 7) | ((led_details->data_en& 0x1) << 6)
		| ((led_details->burst_cycle& 0x3) << 2) | (led_details->clk_cycle& 0x3);
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write_mask(lchip, param, 0xa004, val, 0x01cf));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_led_glb_config(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    mars_led_details_t* led_details;
    uint16 val1 = 0;
    uint16 val4 = 0;

    led_details = (mars_led_details_t*)pv_arg;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param,0xa001, &val1));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param,0xa004, &val4));

    led_details->act_low = (val1 >> 11) & 0x1;
    led_details->bit_mask= (val1 >> 8) & 0x7;
    led_details->port_en_ctrl= val1 & 0xff;
    led_details->clk_en= (val4 >> 7) & 0x1;
    led_details->data_en= (val4 >> 6) & 0x1;
    led_details->burst_cycle= (val4 >> 2) & 0x3;
    led_details->clk_cycle= val4 & 0x3;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_led_serial(uint8 lchip, ctc_chip_mdio_para_t* param, void* serial)
{
    uint16 loop = 0;
    uint16 reg = 0xa077;
    mars_led_serial_t* led_serial;
    uint16 serial_val = 0;

    led_serial = (mars_led_serial_t*)serial;
    for(loop = 0;loop < MARS_SERIAL_LED_NUM_MAX;loop++)
    {
        serial_val = ((led_serial->port_num & 0x7) << 4) | (led_serial->led_id& 0x3);
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write(lchip, param, reg - loop, serial_val));
        led_serial += 1;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_led_serial(uint8 lchip, ctc_chip_mdio_para_t* param, void* serial)
{
    int32 loop = 0;
    uint16 reg = 0xa077;
    mars_led_serial_t* led_serial;
    uint16 serial_val = 0;

    led_serial = (mars_led_serial_t*)serial;

    for(loop = 0;loop < MARS_SERIAL_LED_NUM_MAX;loop++)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param, reg - loop, &serial_val));
        led_serial->port_num = (serial_val >> 4) & 0x7;
        led_serial->led_id= serial_val & 0x3;
        led_serial += 1;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_led_blink(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 val)
{
    uint16 blink_val = 0;
    uint16 force_val = 0;
    uint16 reg = 0;

    blink_val = val & MARS_LED_BLK_MASK;
    if(val & MARS_LED_NUM_0)
    {
        reg = 0xb8;
    }
    else if(val & MARS_LED_NUM_1)
    {
        reg = 0xb9;
    }
    else if(val & MARS_LED_NUM_2)
    {
        reg = 0xbb;
    }
    else
    {
        return CTC_E_INVALID_PARAM;
    }

    if(val & MARS_LED0_FORCE_EN)
    {
        force_val |= 0x5;
    }
    if(val & MARS_LED1_FORCE_EN)
    {
        force_val |= 0x28;
    }
    if(val & MARS_LED2_FORCE_EN)
    {
        force_val |= 0x140;
    }

    if(val & MARS_LED_FIBER_PORT)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_FIBER_LED, reg, blink_val));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_FIBER_LED, 0xb7, force_val));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_UTP, reg, blink_val));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, MARS_PAGE_UTP, 0xb7, force_val));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_led_blink(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* val)
{
    uint32 result_val = 0;
    uint16 blink_val = 0;
    uint16 force_val = 0;
    uint16 reg = 0xb8;

    result_val = *val;
    if(result_val & MARS_LED_NUM_0)
    {
        reg = 0xb8;
    }
    else if(result_val & MARS_LED_NUM_1)
    {
        reg = 0xb9;
    }
    else if(result_val & MARS_LED_NUM_2)
    {
        reg = 0xbb;
    }
    else
    {
        return CTC_E_INVALID_PARAM;
    }

    if(result_val & MARS_LED_FIBER_PORT)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_FIBER_LED, reg, &blink_val));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_FIBER_LED, 0xb7, &force_val));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, reg, &blink_val));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0xb7, &force_val));
    }

    result_val |= (blink_val & 0x3fff);
    if(force_val & 0x5)
        result_val |= MARS_LED0_FORCE_EN;
    if(force_val & 0x28)
        result_val |= MARS_LED1_FORCE_EN;
    if(force_val & 0x140)
        result_val |= MARS_LED2_FORCE_EN;

    *val = result_val;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_led_blink_act(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    mars_led_blink_act_t* led_blink_etc;
    uint16 blink_val = 0;
    uint16 page = 0;
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    led_blink_etc = (mars_led_blink_act_t*)pv_arg;

    blink_val = ((led_blink_etc->led_blk_duty_cycle & 0x7) << 4) | ((led_blink_etc->led_blk_freq & 0x3) << 2)
		| (led_blink_etc->led_blk_freq & 0x3);
    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
    {
        page = MARS_PAGE_FIBER_LED;
    }
    else
    {
        page = MARS_PAGE_UTP;
    }
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip, param, page, 0xba, blink_val));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_led_blink_act(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    mars_led_blink_act_t* led_blink_etc;
    uint16 blink_val = 0;
    uint16 blink_mode = 0;
    uint16 page = 0;
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    led_blink_etc = (mars_led_blink_act_t*)pv_arg;
    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
    {
        page = MARS_PAGE_FIBER_LED;
    }
    else
    {
        page = MARS_PAGE_UTP;
    }

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, page, 0xb7, &blink_val));
    blink_mode = (blink_val >> 15) & 0x1;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, page, 0xba, &blink_val));
    led_blink_etc->led_blk_duty_cycle = (blink_val >> 4) & 0x7;
    if(blink_mode)
    {
        led_blink_etc->led_blk_freq= (blink_val >> 2) & 0x3;
    }
    else
    {
        led_blink_etc->led_blk_freq= blink_val & 0x3;
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_jumbo_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    if(enable)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x0, 0x0020, 0x0020));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x0, 0x8000, 0x8000));
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_UTP, 0x0, 0x0000, 0x0020));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip, param, MARS_PAGE_UTP, 0x0, 0x8000, 0x8000));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_jumbo_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    uint16 val;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_UTP, 0x0, &val));
    if(val & 0x20)
    {
        *p_enable= GLB_ENABLE;
    }
    else
    {
        *p_enable= GLB_DISABLE;
    }

    return CTC_E_NONE;
}

int32
mars4c_set_synce(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable, uint32 freq,uint16* value)
{
    uint16 val = 0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);
    val = *value;

    if(enable)
    {
        if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
        {
            val |= 0x1 << (phyaddr - baseaddr + 4);
        }
        else
        {
            val |= 0x1 << (phyaddr - baseaddr);
        }

        if(freq == MARS_SYNCE_FREQ_25MHZ)
        {
            val |= 0x8000;
            val &= 0xdbff;
        }
        else if(freq == MARS_SYNCE_FREQ_31P25MHZ)
        {
            val |= 0x8400;
            val &= 0xdfff;
        }
        else if(freq == MARS_SYNCE_FREQ_125MHZ)
        {
            val |= 0xa000;
            val &= 0xfbff;
        }
        else if(freq == MARS_LOCAL_FREQ_25MHZ)
        {
            val |= 0xa400;
        }
        else
        {
            return ctc_phy_common_unsupport();
        }
    }
    else
    {
        val = 0x0;
    }

    *value = val;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_synce_en(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    int32 check = CTC_E_NONE;
    uint16 val = 0;
    uint16 reg = 0;
    mars_synce_t* synce;

    synce = (mars_synce_t*)pv_arg;
    if(synce->channel == 0)
    {
        reg = 0xa006;
    }
    else if(synce->channel == 1)
    {
        reg = 0xa00e;
    }
    else
    {
        return ctc_phy_common_unsupport();
    }

    check = mars4c_set_synce(lchip,param,synce->enable,synce->freq,&val);
    if(check == CTC_E_FEATURE_NOT_SUPPORT)
    {
        return ctc_phy_common_unsupport();
    }

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write(lchip, param,reg,val));

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_synce_en(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    mars_synce_t* synce;
    uint16 val = 0;
    uint16 reg = 0;
    uint16 freq = 0;
    uint16 phyaddr = 0;
    uint16 baseaddr = 0;
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    phyaddr = param->phy_addr;
    baseaddr = ctc_phy_common_get_base_addr(g_phy_port_info,param);
    synce = (mars_synce_t*)pv_arg;

    if(synce->channel == 0)
    {
        reg = 0xa006;
    }
    else if(synce->channel == 1)
    {
        reg = 0xa00e;
    }
    else
    {
        return ctc_phy_common_unsupport();
    }
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip, param,reg,&val));

    if(g_phy_port_info[port_id].port_type == MARS_PORT_TYPE_FIBER)
    {
        if((val & 0x8000) && (val & (0x1 << (phyaddr-baseaddr + 4))))
        {
            synce->enable = GLB_ENABLE;
        }
        else
        {
            synce->enable = GLB_DISABLE;
        }
    }
    else
    {
        if((val & 0x8000) && (val & (0x1 << (phyaddr-baseaddr))))
        {
            synce->enable = GLB_ENABLE;
        }
        else
        {
            synce->enable = GLB_DISABLE;
        }
    }

    freq = ((val >> 12) & 0x2) | ((val >> 10) & 0x1);
    synce->freq= freq;

    return CTC_E_NONE;
}

uint32
mars4c_get_prbs_type(uint16 val)
{
    if((val & 0x1e0) == 0x0)
    {
        return MARS_TEST_MODE_PRBS7;
    }
    else if((val & 0x1e0) == 0x20)
    {
        return MARS_TEST_MODE_PRBS10;
    }
    else if((val & 0x1e0) == 0x100)
    {
        return MARS_TEST_MODE_PRBS31;
    }
    else
    {
        return MARS_TEST_MODE_MAX;
    }
}

int32
ctc_phy_mars4c_set_prbs_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable, uint32 prbs)
{
    if(enable)
    {
        if(prbs == MARS_TEST_MODE_PRBS7)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_QSGMII, 0x5, 0x8000, 0x81e0));
        }
        else if(prbs == MARS_TEST_MODE_PRBS10)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_QSGMII, 0x5, 0x8020, 0x81e0));
        }
        else if(prbs == MARS_TEST_MODE_PRBS31)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_QSGMII, 0x5, 0x8100, 0x81e0));
        }
        else
        {
            return ctc_phy_common_unsupport();
        }
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_QSGMII, 0x5, 0x0000, 0x8000));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_prbs_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable, uint32* p_prbs)
{
    uint16 val;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_QSGMII,0x5,&val));

    *p_enable = (val & 0x8000) ? GLB_ENABLE : GLB_DISABLE;
    *p_prbs = mars4c_get_prbs_type(val);

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_prbs_check_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable, uint32 prbs)
{
    if(enable)
    {
        if(prbs == MARS_TEST_MODE_PRBS7)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_QSGMII, 0x5, 0x4000, 0x41e0));
        }
        else if(prbs == MARS_TEST_MODE_PRBS10)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_QSGMII, 0x5, 0x4020, 0x41e0));
        }
        else if(prbs == MARS_TEST_MODE_PRBS31)
        {
            PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_QSGMII, 0x5, 0x4100, 0x41e0));
        }
        else
        {
            return ctc_phy_common_unsupport();
        }
    }
    else
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write_mask(lchip, param, MARS_PAGE_QSGMII, 0x5, 0x0000, 0x4000));
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_prbs_check_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable, uint32* p_prbs)
{
    uint16 val;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_QSGMII,0x5,&val));

    *p_enable = (val & 0x4000) ? GLB_ENABLE : GLB_DISABLE;
    *p_prbs = mars4c_get_prbs_type(val);

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_get_prbs_result(uint8 lchip, ctc_chip_mdio_para_t* param, void* pv_arg)
{
    uint16 val,error_high,error_low;
    mars_prbs_result_t* prbs_result;

    prbs_result = (mars_prbs_result_t*)pv_arg;
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip, param, MARS_PAGE_QSGMII,0x5,&val));
    prbs_result->prbs= mars4c_get_prbs_type(val);

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip,param, MARS_PAGE_QSGMII,0x8,&val));
    prbs_result->sync= (val & 0x1) ? MARS_SYNC: MARS_OUT_SYNC;

    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip,param, MARS_PAGE_QSGMII,0x9,&error_low));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip,param, MARS_PAGE_QSGMII,0xa,&error_high));
    prbs_result->error= (error_high << 16) | error_low;

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_test_mode(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 mode, uint32 speed)
{
    uint8 port_id;

    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    if (g_phy_port_info[port_id].port_type != MARS_PORT_TYPE_COPPER)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x8140, 0xb140)); /* force speed */
    }
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_sleep_mode_en(lchip, param, GLB_DISABLE));
    PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x10, 0x0002));

    if (speed == GLB_SPEED_1G)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x8140, 0xb140)); /* force speed */
    }
    else if (speed == GLB_SPEED_100M)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0xa100, 0xb140)); /* force speed */
    }
    else if (speed == GLB_SPEED_10M)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write_mask(lchip,param, MARS_PAGE_UTP, PHY_CTL_REG, 0x8100, 0xb140)); /* force speed */
    }

    if(mode == MARS_TEST_MODE_DISABLE)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x9, 0x0600));
        PHY_MARS_ERROR_RETURN(mars4c_config_recover(lchip,param));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x10, 0x0062));
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_sleep_mode_en(lchip, param, GLB_ENABLE));
    }
    else if(mode == MARS_TEST_MODE_1)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x9, 0x2200));
    }
    else if(mode == MARS_TEST_MODE_2)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x9, 0x5a00));
    }
    else if(mode == MARS_TEST_MODE_3)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x9, 0x7200));
    }
    else if(mode == MARS_TEST_MODE_4)
    {
        PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip, param, MARS_PAGE_UTP, 0x9, 0x8200));
    }
    else
    {
        return ctc_phy_common_unsupport();
    }

    return CTC_E_NONE;
}

int32
ctc_phy_mars4c_set_ext_attr(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value)
{
    return CTC_E_NONE;

    switch (type)
    {
        case PHY_SET_PKT_CK:
        {
		packet_checker_t* pktck;
		uint32 enable;
		uint32 stream;

		pktck = (packet_checker_t*)p_value;
		enable = pktck->enable;
		stream = pktck->stream;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_packet_checker(lchip,param,enable,stream));
              return CTC_E_NONE;
        }
        case PHY_SET_PKT_GEN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_packet_gen(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_SET_PKT_GEN_EN:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_packet_gen_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_VCT_EN:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_vct_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_MDIMDIX_MODE:
        {
		uint32 mode;

		mode = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_mdi_mdix_mode(lchip,param,mode));
              return CTC_E_NONE;
        }
        case PHY_SET_DOWNGRADE_EN:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_downgrade_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_FASTLINKDOWN:
        {
		fast_link_down_t* fast_link_down;
		uint32 enable;
		uint32 delay;

		fast_link_down = (fast_link_down_t*)p_value;
		enable = fast_link_down->enable;
		delay = fast_link_down->delay;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_fast_link_down(lchip,param,enable,delay));
              return CTC_E_NONE;
        }
        case PHY_SET_LDS_EN:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_lds_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_LED_EN:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_led_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_LED_MODE:
        {
		uint32 mode;

		mode = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_led_mode(lchip,param,mode));
              return CTC_E_NONE;
        }
        case PHY_SET_LED_GLB_CONFIG:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_led_glb_config(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_SET_LED_SERIAL:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_led_serial(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_SET_LED_BLINK:
        {
		uint32 val;

		val = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_led_blink(lchip,param,val));
              return CTC_E_NONE;
        }
        case PHY_SET_LED_BLINK_ACT:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_led_blink_act(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_SET_JUMBO:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_jumbo_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_SYNCE:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_synce_en(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_SET_PRBS:
        {
		prbs_en_t* prbs_en;
		uint32 enable;
		uint32 prbs;

		prbs_en = (prbs_en_t*)p_value;
		enable = prbs_en->enable;
		prbs = prbs_en->prbs;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_prbs_en(lchip,param,enable,prbs));
              return CTC_E_NONE;
        }
        case PHY_SET_PRBS_CK:
        {
		prbs_en_t* prbs_en;
		uint32 enable;
		uint32 prbs;

		prbs_en = (prbs_en_t*)p_value;
		enable = prbs_en->enable;
		prbs = prbs_en->prbs;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_prbs_check_en(lchip,param,enable,prbs));
              return CTC_E_NONE;
        }
        case PHY_SET_TESTMODE:
        {
		test_mode_t* test;

		test = (test_mode_t*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_test_mode(lchip,param,test->mode,test->speed));
              return CTC_E_NONE;
        }
        case PHY_EXT_WRITE:
        {
		phy_ext_t* phy_ext;
		uint32 reg;
		uint32 value;

		phy_ext = (phy_ext_t*)p_value;
		reg = phy_ext->reg;
		value = phy_ext->value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_write(lchip,param,reg,value));
              return CTC_E_NONE;
        }
        case PHY_PAGE_WRITE:
        {
		phy_page_ext_t* phy_ext;
		uint32 reg;
		uint32 value;
		uint32 page;

		phy_ext = (phy_page_ext_t*)p_value;
		reg = phy_ext->reg;
		value = phy_ext->value;
		page = phy_ext->page;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_write(lchip,param,page,reg,value));
              return CTC_E_NONE;
        }
        case PHY_PAGE_EXT_WRITE:
        {
		phy_page_ext_t* phy_ext;
		uint32 reg;
		uint32 value;
		uint32 page;

		phy_ext = (phy_page_ext_t*)p_value;
		reg = phy_ext->reg;
		value = phy_ext->value;
		page = phy_ext->page;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_write(lchip,param,page,reg,value));
              return CTC_E_NONE;
        }
        case PHY_SET_SLEEP_EN:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_sleep_mode_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_EEE_EN:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_eee_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_FIB_TO_SGMII_EN:
        {
		uint32 enable;

		enable = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_fiber_to_sgmii_en(lchip,param,enable));
              return CTC_E_NONE;
        }
        case PHY_SET_CHIP_MODE:
        {
		uint32 mode;

		mode = *(uint32*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_set_chip_mode(lchip,param,mode));
              return CTC_E_NONE;
        }
        default:
        	return CTC_E_INVALID_PARAM;
    }
}

int32
ctc_phy_mars4c_get_ext_attr(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value)
{
    int32 *p;

    p = (int32*)p_value;
    *p = 0;
    return CTC_E_NONE;

    switch (type)
    {
        case PHY_GET_PKT_CK:
        {
		packet_checker_t* pktck;
		pktck = (packet_checker_t*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_packet_checker(lchip,param,&pktck->enable,&pktck->stream));
              return CTC_E_NONE;
        }
        case PHY_GET_PKT_COUNT:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_packet_count(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_PKT_GEN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_packet_gen(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_PKT_GEN_EN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_packet_gen_en(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_VCT_RESULT:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_vct_result(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_LINK_STATUS_DETAILS:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_link_status_details(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_MDIMDIX_MODE:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_mdi_mdix_mode(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_DOWNGRADE_EN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_downgrade_en(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_FASTLINKDOWN:
        {
		fast_link_down_t* fastld;
		fastld = (fast_link_down_t*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_fast_link_down(lchip,param,&fastld->enable,&fastld->delay));
              return CTC_E_NONE;
        }
        case PHY_GET_LDS_EN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_lds_en(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_LDS_RESULT:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_lds_details(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_LED_EN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_led_en(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_LED_MODE:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_led_mode(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_LED_GLB_CONFIG:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_led_glb_config(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_LED_SERIAL:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_led_serial(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_LED_BLINK:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_led_blink(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_LED_BLINK_ACT:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_led_blink_act(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_JUMBO:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_jumbo_en(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_SYNCE:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_synce_en(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_PRBS:
        {
		prbs_en_t* prbsen;
		prbsen = (prbs_en_t*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_prbs_en(lchip,param,&prbsen->enable,&prbsen->prbs));
              return CTC_E_NONE;
        }
        case PHY_GET_PRBS_CK:
        {
		prbs_en_t* prbsck;
		prbsck = (prbs_en_t*)p_value;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_prbs_check_en(lchip,param,&prbsck->enable,&prbsck->prbs));
              return CTC_E_NONE;
        }
        case PHY_GET_PRBS_RESULT:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_prbs_result(lchip,param,p_value));
              return CTC_E_NONE;
        }
        case PHY_EXT_READ:
        {
		uint32 reg;
		phy_ext_t* phy_ext;
		phy_ext = (phy_ext_t*)p_value;
		reg = phy_ext->reg;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_ext_read(lchip,param,reg,&phy_ext->value));
              return CTC_E_NONE;
        }
        case PHY_PAGE_READ:
        {
		uint32 reg;
		uint32 page;
		phy_page_ext_t* phy_ext;
		phy_ext = (phy_page_ext_t*)p_value;
		page = phy_ext->page;
		reg = phy_ext->reg;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_read(lchip,param,page,reg,&phy_ext->value));
              return CTC_E_NONE;
        }
        case PHY_PAGE_EXT_READ:
        {
		uint32 reg;
		uint32 page;
		phy_page_ext_t* phy_ext;
		phy_ext = (phy_page_ext_t*)p_value;
		page = phy_ext->page;
		reg = phy_ext->reg;
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_page_ext_read(lchip,param,page,reg,&phy_ext->value));
              return CTC_E_NONE;
        }
        case PHY_GET_SLEEP_EN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_sleep_mode_en(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_EEE_EN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_eee_en(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_EEE_STATUS:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_eee_status(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_FIB_TO_SGMII_EN:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_fiber_to_sgmii_en(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        case PHY_GET_CHIP_MODE:
        {
        	PHY_MARS_ERROR_RETURN(ctc_phy_mars4c_get_chip_mode(lchip,param,(uint32*)p_value));
              return CTC_E_NONE;
        }
        default:
        	return CTC_E_INVALID_PARAM;
    }
}

/**
@ingroup DRVTBL
@details This is the driver for mars4c.
*/
ctc_phy_driver_t ctc_chip_phy_mars4c_api =
{
    .init = ctc_phy_mars4c_init,
    .deinit = ctc_phy_mars4c_deinit,
    .set_port_en = ctc_phy_mars4c_set_port_en,
    .get_port_en = ctc_phy_mars4c_get_port_en,
    .set_port_duplex_en = ctc_phy_mars4c_set_port_duplex_en,
    .get_port_duplex_en = ctc_phy_mars4c_get_port_duplex_en,
    .set_port_speed = ctc_phy_mars4c_set_port_speed,
    .get_port_speed = ctc_phy_mars4c_get_port_speed,
    .set_port_auto_neg_en = ctc_phy_mars4c_set_port_auto_neg_en,
    .get_port_auto_neg_en = ctc_phy_mars4c_get_port_auto_neg_en,
    .set_port_loopback = ctc_phy_mars4c_set_port_loopback,
    .get_port_loopback = ctc_phy_mars4c_get_port_loopback,
    .get_link_up_status = ctc_phy_mars4c_get_link_up_status,
    .linkup_event = ctc_phy_mars4c_linkup_event,
    .linkdown_event = ctc_phy_mars4c_linkdown_event,
    .set_port_unidir_en = ctc_phy_mars4c_set_port_unidir_en,
    .get_port_unidir_en =ctc_phy_mars4c_get_port_unidir_en,
    .set_port_medium = ctc_phy_mars4c_set_port_medium,
    .get_port_medium = ctc_phy_mars4c_get_port_medium,
    .set_ext_attr = ctc_phy_mars4c_set_ext_attr,
    .get_ext_attr = ctc_phy_mars4c_get_ext_attr,
};

/**
@fn int32 ctc_phy_driver_get_mars4c(void *drv)
@details This function will be called in ctc_app_phy_init for register driver for mars4c.
@return the driver interface about mars4c.
*/
int32
ctc_phy_driver_get_mars4c(void **drv)
{
    *drv = (void*)(&ctc_chip_phy_mars4c_api);
    return 0;
}
