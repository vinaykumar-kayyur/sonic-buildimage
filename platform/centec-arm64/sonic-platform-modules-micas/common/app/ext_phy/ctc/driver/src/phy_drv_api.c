/**
 @file phy_drv_api.c
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/
#include "sal.h"
#include "phy_drv_def.h"
#include "phy_drv_common.h"
#include "phy_drv_api.h"

phy_info_t g_phy_port_info[CTC_MAX_PHY_PORT_NUM];

phy_manufacturers_t phy_manuf_ids[] = {
#ifdef SUPPORT_PHY_VSC8512
	{PHY_TYPE_VSC8512_A,0xffffffff, "vsc8512",ctc_phy_driver_get_vsc8512},
	{PHY_TYPE_VSC8512_B, 0xffffffff, "vsc8512",ctc_phy_driver_get_vsc8512},
#endif
#ifdef SUPPORT_PHY_MV88E1680
    {PHY_TYPE_MV88E1680, 0xffffffff, "mv88e1680",ctc_phy_driver_get_mv88e1680},
#endif
#ifdef SUPPORT_PHY_MARS
    {PHY_TYPE_MARS8P, 0xffffffff, "mars8p",ctc_phy_driver_get_mars8p},
    {PHY_TYPE_MARS4C, 0xffffffff, "mars4c",ctc_phy_driver_get_mars4c},
    {PHY_TYPE_MARS1S, 0xfffffff0, "mars1s",ctc_phy_driver_get_mars1s},
    {PHY_TYPE_MARS1S_V1, 0xfffffff0, "mars1s",ctc_phy_driver_get_mars1s},
#endif
#ifdef SUPPORT_PHY_RTL8218B
    {PHY_TYPE_RTL8128B, 0xffffffff, "rtl8218b",ctc_phy_driver_get_rtl8218b},
#endif
	{PHY_TYPE_UNKNOWN, 0xffffffff, "Unknown",NULL}
};

uint8
ctc_phy_driver_num(void)
{
    return sizeof(phy_manuf_ids)/sizeof(phy_manufacturers_t);
}

int32
ctc_phy_mdio_para_find(uint32 gport, ctc_chip_mdio_para_t *para)
{
    sal_memset(para, 0, sizeof(ctc_chip_mdio_para_t));
    para->bus = g_phy_port_info[gport].bus;
    para->phy_addr = g_phy_port_info[gport].phy_addr;
    return 0;
}

int32
ctc_phy_driver_find(uint8 lchip,uint32 gport, ctc_phy_driver_t **drv)
{
    int8 i = 0;
    int32 ret = CTC_E_NONE;
    phy_manufacturers_t *phy;
    ctc_phy_driver_t *phy_drv = NULL;
    ctc_chip_mdio_para_t para;
    uint32 phy_id;
    uint8 found = 0;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_common_probe_id(lchip,&para,&phy_id);
    for(i = 0;i<sizeof(phy_manuf_ids)/sizeof(phy_manufacturers_t);i++)
    {
        phy = &phy_manuf_ids[i];
        if(phy->id !=PHY_TYPE_UNKNOWN && phy->driver_get != NULL)
        {
            if((phy->id&phy->id_mask)==(phy_id&phy->id_mask))
            {
                phy->driver_get((void*)&phy_drv);
                found = 1;
                break;
            }
        }
    }
    if(found)
    {
        if(phy_drv != NULL)
        {
            *drv = (ctc_phy_driver_t *)phy_drv;
        }
    }
    return ret;
}

/**
 @fn int32 ctc_phy_init(uint8 lchip_id, uint32 gport)
 @ingroup APP_API
 @details This function will do phy initialization for specified port by call driver inteface
    "int32 (* init)(uint8 lchip, ctc_chip_mdio_para_t* param)" register for this port according to the phy type.
    For some special phy, you may need do pre-init before this function by call
    ctc_phy_set_port_ext_attr(lchip_id, gport, PHY_CUSTOM_PREINIT, 1), some other special phy, you may need do post-init
    after this function by call ctc_phy_set_port_ext_attr(lchip_id, gport, PHY_CUSTOM_POSTINIT, 1).
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @return if success return 0 or return error no.
*/
int32
ctc_phy_init(uint8 lchip_id, uint32 gport)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->init(lchip_id,&para);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_set_port_en(uint8 lchip_id, uint32 gport,uint32 enable)
 @ingroup APP_API
 @details This function will do phy enable for specified port by call driver inteface
    "int32 (* set_port_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)"  register for this port according to the phy type.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] enable value for port enable
 @return if success return 0 or return error no.
*/
int32
ctc_phy_set_port_en(uint8 lchip_id, uint32 gport,uint32 enable)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->set_port_en(lchip_id,&para,enable);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_port_en(uint8 lchip_id, uint32 gport,uint32* enable)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_port_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)"
    register for this port according to the phy type and return the enable status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[out] enable point to value for the specified port enable status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_port_en(uint8 lchip_id, uint32 gport,uint32* enable)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_port_en(lchip_id,&para,enable);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_set_port_duplex(uint8 lchip_id, uint32 gport,uint32 duplex)
 @ingroup APP_API
 @details This function will do phy duplex setting for specified port by call driver inteface
    "int32 (* set_port_duplex_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)"
    register for this port according to the phy type.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] duplex value for port duplex
 @return if success return 0 or return error no.
*/
int32
ctc_phy_set_port_duplex(uint8 lchip_id, uint32 gport,uint32 duplex)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->set_port_duplex_en(lchip_id,&para,duplex);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_port_duplex(uint8 lchip_id, uint32 gport,uint32* duplex)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_port_duplex_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)"
    register for this port according to the phy type and return the duplex status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[out] duplex point to value for the specified port duplex status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_port_duplex(uint8 lchip_id, uint32 gport,uint32* duplex)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_port_duplex_en(lchip_id,&para,duplex);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_set_port_speed(uint8 lchip_id, uint32 gport,uint32 speed)
 @ingroup APP_API
 @details This function will do phy speed setting for specified port by call driver inteface
    "int32 (* set_port_speed)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 value)"
    register for this port according to the phy type.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] speed value for port speed
 @return if success return 0 or return error no.
*/
int32
ctc_phy_set_port_speed(uint8 lchip_id, uint32 gport,uint32 speed)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->set_port_speed(lchip_id,&para,speed);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_port_speed(uint8 lchip_id, uint32 gport,uint32* speed)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_port_speed)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_value)"
    register for this port according to the phy type and return the speed status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[out] speed point to value for the specified port speed status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_port_speed(uint8 lchip_id, uint32 gport,uint32* speed)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_port_speed(lchip_id,&para,speed);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_set_port_auto_neg(uint8 lchip_id, uint32 gport,uint32 enable)
 @ingroup APP_API
 @details This function will do phy auto-negotiation setting for specified port by call driver inteface
    "int32 (* set_port_auto_neg_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)"
    register for this port according to the phy type.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] enable value for port auto-negotiation
 @return if success return 0 or return error no.
*/
int32
ctc_phy_set_port_auto_neg(uint8 lchip_id, uint32 gport,uint32 enable)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->set_port_auto_neg_en(lchip_id,&para,enable);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_port_auto_neg(uint8 lchip_id, uint32 gport,uint32* enable)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_port_auto_neg_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)"
    register for this port according to the phy type and return the auto-negotiation status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[out] enable point to value for the specified port auto-negotiation status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_port_auto_neg(uint8 lchip_id, uint32 gport,uint32* enable)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_port_auto_neg_en(lchip_id,&para,enable);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_set_port_loopback(uint8 lchip_id, uint32 gport,uint32 value)
 @ingroup APP_API
 @details This function will do phy loopback setting for specified port by call driver inteface
    "int32 (* set_port_loopback)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)"
    register for this port according to the phy type.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] value value for port loopback mode
 @return if success return 0 or return error no.
*/
int32
ctc_phy_set_port_loopback(uint8 lchip_id, uint32 gport,uint32 value)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->set_port_loopback(lchip_id,&para,value);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_port_loopback(uint8 lchip_id, uint32 gport,uint32* value)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_port_loopback)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)"
    register for this port according to the phy type and return the loopback status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[out] value point to value for the specified port loopback status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_port_loopback(uint8 lchip_id, uint32 gport,uint32* value)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_port_loopback(lchip_id,&para,value);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_link_up_status(uint8 lchip_id, uint32 gport,uint32* value)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_link_up_status)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_link_up)"
    register for this port according to the phy type and return the link up status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[out] value point to value for the specified port link up status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_link_up_status(uint8 lchip_id, uint32 gport,uint32* value)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_link_up_status(lchip_id,&para,value);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_set_port_unidir(uint8 lchip_id, uint32 gport,uint32 enable)
 @ingroup APP_API
 @details This function will do phy unidirection for specified port by call driver inteface
    "int32 (* set_port_unidir_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)"
    register for this port according to the phy type.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] enable value for port unidirection.
 @return if success return 0 or return error no.
*/
int32
ctc_phy_set_port_unidir(uint8 lchip_id, uint32 gport,uint32 enable)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->set_port_unidir_en(lchip_id,&para,enable);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_port_unidir(uint8 lchip_id, uint32 gport,uint32* enable)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_port_unidir_en)(uint8 lchip, ctc_chip_mdio_para_t* param,  uint32* p_enable)"
    register for this port according to the phy type and return the unidirection status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[out] enable point to value for the specified port unidirection status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_port_unidir(uint8 lchip_id, uint32 gport,uint32* enable)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_port_unidir_en(lchip_id,&para,enable);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_set_port_medium(uint8 lchip_id, uint32 gport,uint32 value)
 @ingroup APP_API
 @details This function will do phy medium for specified port by call driver inteface
    "int32 (* set_port_medium)(uint8 lchip, ctc_chip_mdio_para_t* param,  uint32 value)"
    register for this port according to the phy type.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] value value for port medium mode
 @return if success return 0 or return error no.
*/
int32
ctc_phy_set_port_medium(uint8 lchip_id, uint32 gport,uint32 value)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->set_port_medium(lchip_id,&para,value);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_port_medium(uint8 lchip_id, uint32 gport,uint32* value)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_port_medium)(uint8 lchip, ctc_chip_mdio_para_t* param,  uint32* p_value)"
    register for this port according to the phy type and return the medium status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[out] value point to value for the specified port medium status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_port_medium(uint8 lchip_id, uint32 gport,uint32* value)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_port_medium(lchip_id,&para,value);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_set_port_ext_attr(uint8 lchip_id, uint32 gport,uint32 type,void* p_value)
 @ingroup APP_API
 @details This function will do phy specified property for specified port by call driver inteface
    "int32 (* set_port_medium)(uint8 lchip, ctc_chip_mdio_para_t* param,  void* value)"
    register for this port according to the phy type.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] type property type
 @param[in] p_value value for port specified property
 @return if success return 0 or return error no.
*/
int32
ctc_phy_set_port_ext_attr(uint8 lchip_id, uint32 gport,uint32 type, void* p_value)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->set_ext_attr(lchip_id,&para,type,p_value);
    }
    return ret;
}

/**
 @fn int32 ctc_phy_get_port_ext_attr(uint8 lchip_id, uint32 gport,uint32 type,void* p_value)
 @ingroup APP_API
 @details This function will call driver inteface "int32 (* get_ext_attr)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value)"
    register for this port according to the phy type and return the specified property type status for specified port.
 @param[in] lchip_id asic chip id
 @param[in] gport port index
 @param[in] type property type
 @param[out] p_value point to value for the specified port of specified property type status
 @return if success return 0 or return error no.
*/
int32
ctc_phy_get_port_ext_attr(uint8 lchip_id, uint32 gport,uint32 type, void* p_value)
{
    int32 ret = 0;
    ctc_phy_driver_t *drv = NULL;
    ctc_chip_mdio_para_t para;
    ret += ctc_phy_mdio_para_find(gport,&para);
    ret += ctc_phy_driver_find(lchip_id,gport,&drv);
    if(drv!=NULL)
    {
        ret += drv->get_ext_attr(lchip_id,&para,type,p_value);
    }
    return ret;
}
