/**
 @file phy_drv_mars1s.c
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/
#include "sal.h"
#include "phy_drv_common.h"
#include "phy_drv_api.h"

extern phy_info_t g_phy_port_info[CTC_MAX_PHY_PORT_NUM];

/*****************************************************************************/
static int32
mars1s_reg_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint8 reg, uint16* value)
{
    int32 ret = CTC_E_NONE;
    param->reg = reg;
    ret = ctc_phy_mdio_read(lchip,CTC_CHIP_MDIO_GE,param);
    PHY_DEBUG_PRINT("phy addr %d: read reg 0x%x: 0x%x\n", param->phy_addr, param->reg, param->value);
    if (ret < 0)
    {
        PHY_LOG_ERR("%% mars1s_reg_read fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }
    *value = param->value;
    return CTC_E_NONE;
}

static int32
mars1s_reg_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint8 reg, uint16 value)
{
    int32 ret = CTC_E_NONE;
    param->reg = reg;
    param->value = value;
    ret = ctc_phy_mdio_write(lchip,CTC_CHIP_MDIO_GE,param);
    PHY_DEBUG_PRINT("phy addr %d: write reg 0x%x: 0x%x\n", param->phy_addr, param->reg,param->value);
    if (ret < 0)
    {
        PHY_LOG_ERR("%% mars1s_reg_write fail, ret = %d!\n", ret);
        return CTC_E_HW_FAIL;
    }
    return CTC_E_NONE;
}

static int32
mars1s_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 value, uint16 mask)
{
    uint16 val;
    int32 ret = CTC_E_NONE;

    ret += mars1s_reg_read(lchip, param, reg, &val);
    value = (value & mask) | (val & ~mask);
    ret += mars1s_reg_write(lchip, param, reg, value);

    return ret;
}

static
int32 mars1s_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 *value)
{
    return mars1s_reg_read(lchip,param,reg,value);
}

static int32 mars1s_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 value)
{
    return mars1s_reg_write(lchip,param,reg,value);;
}

static int32 mars1s_ext_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 *value)
{
    int32 ret = 0;

    ret += mars1s_write(lchip,param,0x1e,reg);
    ret += mars1s_read(lchip,param,0x1f,value);

    return ret;
}
static int32 mars1s_ext_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 value)
{
    int32 ret = 0;

    ret += mars1s_write(lchip,param,0x1e,reg);
    ret += mars1s_write(lchip,param,0x1f,value);

    return ret;
}

static int32
mars1s_ext_write_mask(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 reg, uint16 value, uint16 mask)
{
    int32 ret = 0;
    uint16 val = 0;
    ret += mars1s_ext_read(lchip,param, reg, &val);
    value = (value & mask) | (val & ~mask);
    ret += mars1s_ext_write(lchip,param, reg,value);
    return ret;
}

#if 0
static
int32 mars1s_mmd_read(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 mmdaddr, uint16 reg, uint16 *value)
{
    int32 ret = 0;

    ret += mars1s_write(lchip,param,0xd,mmdaddr);
    ret += mars1s_write(lchip,param,0xe,reg);
    ret += mars1s_write(lchip,param,0xd,0x4000|mmdaddr);
    ret += mars1s_read(lchip,param,0xe,value);

    return ret;
}
static
int32 mars1s_mmd_write(uint8 lchip, ctc_chip_mdio_para_t* param, uint16 mmdaddr, uint16 reg, uint16 value)
{
    int32 ret = 0;

    ret += mars1s_write(lchip,param,0xd,mmdaddr);
    ret += mars1s_write(lchip,param,0xe,reg);
    ret += mars1s_write(lchip,param,0xd,0x4000|mmdaddr);
    ret += mars1s_write(lchip,param,0xe,value);

    return ret;
}
#endif

static int32 mars1s_phy_conf_set(uint8 lchip, ctc_chip_mdio_para_t* param,uint8 speed, uint8 duplex)
{
    int32 ret = 0;
    uint16 reg4=0, reg9=0,reg0_mask =0;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

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
    //if(phy_handle->phy_info.phy_manage_info.flowctrl_ability.symmetric_pause)
    //{
    //    reg4 |= (1<<10);
    //}
    //if(phy_handle->phy_info.phy_manage_info.flowctrl_ability.asymmetric_pause)
    //{
    //    reg4 |= (1<<11);
    //}
    ret += mars1s_write_mask(lchip,param, PHY_AN_ADVERTI_REG, reg4, 0x1de1);
    ret += mars1s_write_mask(lchip,param, PHY_1G_BASET_CTL_REG, reg9, 0x300);
    //ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x1200, 0x1200);

    reg0_mask = 0x2140;
    if (g_phy_port_info[port_id].auto_neg_en == 0) /* Force mode*/
    {
        reg0_mask = 0x3140;/* mask for Auto-Negotiation */
    }
    /* config manual speed with Auto-Negotiation mask */
    if((speed == GLB_SPEED_10M)&&((duplex == GLB_DUPLEX_FULL)||(duplex == GLB_DUPLEX_MAX)))
    {
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x0100, reg0_mask);
    }
    else if((speed == GLB_SPEED_10M)&&(duplex == GLB_DUPLEX_HALF))
    {
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x0000, reg0_mask);
    }
    else if((speed == GLB_SPEED_100M)&&((duplex == GLB_DUPLEX_FULL)||(duplex == GLB_DUPLEX_MAX)))
    {
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x2100, reg0_mask);
    }
    else if((speed == GLB_SPEED_100M)&&(duplex == GLB_DUPLEX_HALF))
    {
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x2000, reg0_mask);
    }
    else if((speed == GLB_SPEED_1G)&&((duplex == GLB_DUPLEX_FULL)||(duplex == GLB_DUPLEX_MAX)))
    {
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x0140, reg0_mask);
    }
    else if((speed == GLB_SPEED_1G)&&(duplex == GLB_DUPLEX_HALF))
    {
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x0040, reg0_mask);
    }
    else /* default speed 1G duplex full */
    {
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x0140, reg0_mask);
    }

    if (g_phy_port_info[port_id].auto_neg_en == 0) /* Force mode*/
    {

        /*When config force mode, need to powerdown and powerup port to notify link parter.*/
        if(g_phy_port_info[port_id].enable)
        {
            ret += mars1s_write_mask(lchip, param, PHY_CTL_REG, 0x0800, 0x0800);
            if(speed == GLB_SPEED_10M)
            {
                sal_udelay(1000000);
            }
            else
            {
                sal_udelay(200000);
            }
            ret += mars1s_write_mask(lchip, param, PHY_CTL_REG, 0x0000, 0x0800);
        }
    }
    else
    {
        /* restart Auto-Negotiation */
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x1200, 0x1200);
    }

    return ret;
}

static int32 mars1s_config_loopback(uint8 lchip, ctc_chip_mdio_para_t* param, uint8 lb_mode)
{
    int32 ret = RESULT_OK;

    switch (lb_mode)
    {
    case GLB_LB_NONE:
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x0000, 0x4000); /* disable internal loopback */
        ret += mars1s_ext_write_mask(lchip,param,0xa,0x00,0x20); /* disable external loopback */
        break;

    case GLB_LB_PHY_FAR:/* external loopback */
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x0000, 0x4000); /* disable internal loopback */
        ret += mars1s_ext_write_mask(lchip,param,0xa,0x20,0x20); /* enable external loopback */
        break;

    case GLB_LB_PHY_NEAR: /* internal loopback */
        ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x4000, 0x4000); /* enable internal loopback */
        ret += mars1s_ext_write_mask(lchip,param,0xa,0x00,0x20); /* disable external loopback */
        break;

    default:
        return RESULT_ERROR;
        break;
    }

    return ret;
}

int32
ctc_phy_mars1s_init(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    int32 ret = CTC_E_NONE;
    uint16 val = 0;
    uint8 port_id;
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
    g_phy_port_info[port_id].speed_status = GLB_SPEED_1G;/* init */
    g_phy_port_info[port_id].mdium_status = g_phy_port_info[port_id].mdium;/* init */
    g_phy_port_info[port_id].loopback_status = g_phy_port_info[port_id].loopback_mode;/* init */
    g_phy_port_info[port_id].undir_status = g_phy_port_info[port_id].undir_en;/* init */

    /* do phy hardware reset per-chip before do phy port init */
    ret += mars1s_ext_read(lchip, param,0xa0ff,&val);
    if (val == 0x5555)
    {
        PHY_DEBUG_PRINT("port %d hardware reset!\n",port_id);
        ret += mars1s_ext_write_mask(lchip,param, 0xa0c0, 0x8000, 0x8000);
        sal_udelay(50000);
        ret += mars1s_ext_write(lchip, param,0xa0ff,0xaaaa);
    }

    /* config whole chip UTP to SGMII mode */
    ret += mars1s_ext_write_mask(lchip, param,0xa001,0x3,0x0007);

    /* enable fast link */
    ret += mars1s_ext_write_mask(lchip, param,0x34,0x000,0x8000);
    ret += mars1s_ext_write_mask(lchip, param,0x37,0xe000,0xe000);

    /* enable interrupt */
    ret += mars1s_ext_write(lchip, param,0xa010,0xffff);
    /* clear interrupt status */
    ret += mars1s_ext_read(lchip, param,0xa011,&val);

    /* keep ext_reg to 0x0000 */
    ret += mars1s_ext_write(lchip, param,0xa000,0);

    /* enable interrupt */
    ret += mars1s_write(lchip, param, 0x12, 0x7800);
    /* clear interrupt status */
    ret += mars1s_read(lchip, param, 0x13, &val);

    /* do phy software reset when do phy port init */
    ret += mars1s_write_mask(lchip,param, PHY_CTL_REG, 0x8000, 0x8000);

    return ret;
}

int32
ctc_phy_mars1s_deinit(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    int32 ret = CTC_E_NONE;

    return ret;
}

int32
ctc_phy_mars1s_set_port_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32 ret = 0;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret = ctc_phy_common_enable_set(lchip, param,enable);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d set enable fail!!",port_id);
    }
    g_phy_port_info[port_id].enable = enable;
    return ret;
}

int32
ctc_phy_mars1s_get_port_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    int32 ret = RESULT_OK;
    uint16 val = 0;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret += mars1s_reg_read(lchip, param, PHY_CTL_REG, &val);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d get enable fail!!",port_id);
    }
    *p_enable =((val>>11)&0x1)?0:1;
    g_phy_port_info[port_id].enable_status = *p_enable;
    return ret;
}

int32
ctc_phy_mars1s_set_port_duplex_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 duplex)
{
    int32 ret = CTC_E_NONE;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret = mars1s_phy_conf_set(lchip, param, phy_speed_ctc2glb(g_phy_port_info[port_id].speed), duplex);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d duplex set fail!!",port_id);
    }
    g_phy_port_info[port_id].duplex = duplex;
    return ret;
}

int32
ctc_phy_mars1s_get_port_duplex_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_duplex)
{
    int32 ret = CTC_E_NONE;
    uint16 val;
    uint32 duplex;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);

    ret += mars1s_read(lchip, param,0x11,&val);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d duplex get fail!!",port_id);
    }
    duplex = (val & 0x2000) ? GLB_DUPLEX_FULL : GLB_DUPLEX_HALF;
    *p_duplex = duplex;
    g_phy_port_info[port_id].duplex_status = duplex;
    return ret;
}

int32
ctc_phy_mars1s_set_port_speed(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 value)
{
    int32 ret = CTC_E_NONE;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret = mars1s_phy_conf_set(lchip, param, phy_speed_ctc2glb(value), g_phy_port_info[port_id].duplex);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d speed set fail!!",port_id);
    }
    g_phy_port_info[port_id].speed = value;

    return ret;
}

int32
ctc_phy_mars1s_get_port_speed(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_value)
{
    int32 ret = CTC_E_NONE;
    uint32 speed = CTC_PORT_SPEED_MAX;
    uint16 value;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret += mars1s_read(lchip, param, 0x11, &value);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d speed get fail!!",port_id);
    }
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
    *p_value = speed;

    g_phy_port_info[port_id].speed_status = speed;
    return ret;
}

int32
ctc_phy_mars1s_set_port_auto_neg_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32 ret = 0;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret = ctc_phy_common_autoNegoEnable_set(lchip, param,enable);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d auto-nego set fail!!",port_id);
    }
    g_phy_port_info[port_id].auto_neg_en = enable;
    return ret;
}

int32
ctc_phy_mars1s_get_port_auto_neg_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    int32 ret = RESULT_OK;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret = ctc_phy_common_autoNegoEnable_get(lchip, param,p_enable);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d auto-nego get fail!!",port_id);
    }
    g_phy_port_info[port_id].auto_neg_status = *p_enable;
    return ret;
}

int32
ctc_phy_mars1s_set_port_loopback(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 mode)
{
    int32 ret = 0;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret = mars1s_config_loopback(lchip, param,mode);
    if (ret != CTC_E_NONE)
    {
        PHY_LOG_ERR("Port %d loopback set fail!!",port_id);
    }
    g_phy_port_info[port_id].loopback_mode = mode;
    return ret;
}

int32
ctc_phy_mars1s_get_port_loopback(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* mode)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    *mode = g_phy_port_info[port_id].loopback_mode;
    return RESULT_OK;
}

int32
ctc_phy_mars1s_get_link_up_status(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_link_up)
{
    int32 ret = CTC_E_NONE;
    uint16 val;
    uint8 linkup;
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    ret += mars1s_ext_write(lchip, param,0xa000,0x0000);
    ret += mars1s_read(lchip, param,0x11,&val);
    linkup = (val & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;

    /*if link down, need read again.*/
    if(linkup == GLB_LINK_DOWN)
    {
        ret += mars1s_read(lchip, param,0x11,&val);
        linkup = (val & 0x400) ? GLB_LINK_UP : GLB_LINK_DOWN;
    }

    *p_link_up = linkup;
    g_phy_port_info[port_id].link_up= linkup;

    return ret;
}

int32
ctc_phy_mars1s_linkup_event(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* user_data)
{
    int32 ret = CTC_E_NONE;
    uint16 val = 0;
    uint32 speed = CTC_PORT_SPEED_MAX;
    /* clear interrupt status */
    mars1s_ext_read(lchip, param,0xa011,&val);
    mars1s_read(lchip, param, 0x13, &val);
    ctc_phy_mars1s_get_port_speed(lchip,param,&speed);

    return ret;
}

int32
ctc_phy_mars1s_linkdown_event(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* user_data)
{
    int32 ret = CTC_E_NONE;
    uint16 val = 0;
    /* clear interrupt status */
    mars1s_ext_read(lchip, param,0xa011,&val);
    mars1s_read(lchip, param, 0x13, &val);

    return ret;
}

int32
ctc_phy_mars1s_set_port_unidir_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type)
{
    return ctc_phy_common_unsupport();
}

int32
ctc_phy_mars1s_get_port_unidir_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* type)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    *type = g_phy_port_info[port_id].undir_en;
    return RESULT_OK;
}

int32
ctc_phy_mars1s_set_port_medium(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type)
{
    return ctc_phy_common_unsupport();
}

int32
ctc_phy_mars1s_get_port_medium(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* type)
{
    uint8 port_id;
    port_id = ctc_phy_common_get_port_id(g_phy_port_info,param);
    *type = g_phy_port_info[port_id].mdium;
    return RESULT_OK;
}

int32
ctc_phy_mars1s_set_ext_attr(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value)
{
    int32 ret = CTC_E_NONE;

    return ret;
}

int32
ctc_phy_mars1s_get_ext_attr(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value)
{
    int32 ret = CTC_E_NONE;

    return ret;
}

/**
@ingroup DRVTBL
@details This is the driver for mars1s.
*/
ctc_phy_driver_t ctc_chip_phy_mars1s_api =
{
    .init = ctc_phy_mars1s_init,
    .deinit = ctc_phy_mars1s_deinit,
    .set_port_en = ctc_phy_mars1s_set_port_en,
    .get_port_en = ctc_phy_mars1s_get_port_en,
    .set_port_duplex_en = ctc_phy_mars1s_set_port_duplex_en,
    .get_port_duplex_en = ctc_phy_mars1s_get_port_duplex_en,
    .set_port_speed = ctc_phy_mars1s_set_port_speed,
    .get_port_speed = ctc_phy_mars1s_get_port_speed,
    .set_port_auto_neg_en = ctc_phy_mars1s_set_port_auto_neg_en,
    .get_port_auto_neg_en = ctc_phy_mars1s_get_port_auto_neg_en,
    .set_port_loopback = ctc_phy_mars1s_set_port_loopback,
    .get_port_loopback = ctc_phy_mars1s_get_port_loopback,
    .get_link_up_status = ctc_phy_mars1s_get_link_up_status,
    .linkup_event = ctc_phy_mars1s_linkup_event,
    .linkdown_event = ctc_phy_mars1s_linkdown_event,
    .set_port_unidir_en = ctc_phy_mars1s_set_port_unidir_en,
    .get_port_unidir_en =ctc_phy_mars1s_get_port_unidir_en,
    .set_port_medium = ctc_phy_mars1s_set_port_medium,
    .get_port_medium = ctc_phy_mars1s_get_port_medium,
    .set_ext_attr = ctc_phy_mars1s_set_ext_attr,
    .get_ext_attr = ctc_phy_mars1s_get_ext_attr,
};

/**
@fn int32 ctc_phy_driver_get_mars1s(void *drv)
@details This function will be called in ctc_app_phy_init for register driver for mars1s.
@return the driver interface about mars1s.
*/
int32
ctc_phy_driver_get_mars1s(void **drv)
{
    *drv = (void*)(&ctc_chip_phy_mars1s_api);
    return 0;
}
