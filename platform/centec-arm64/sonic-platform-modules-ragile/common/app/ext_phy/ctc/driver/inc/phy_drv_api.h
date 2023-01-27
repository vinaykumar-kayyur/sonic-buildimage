/**
 @file phy_drv_api.h
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/

#ifndef __PHY_API_H__
#define __PHY_API_H__

int32 ctc_phy_mdio_read(uint8 lchip_id, ctc_chip_mdio_type_t type, ctc_chip_mdio_para_t* p_para);
int32 ctc_phy_mdio_write(uint8 lchip_id, ctc_chip_mdio_type_t type, ctc_chip_mdio_para_t* p_para);
uint8 ctc_phy_driver_num(void);
int32 ctc_phy_mdio_para_find(uint32 gport, ctc_chip_mdio_para_t *para);
int32 ctc_phy_driver_find(uint8 lchip,uint32 gport, ctc_phy_driver_t **drv);
int32 ctc_phy_init(uint8 lchip_id, uint32 gport);
int32 ctc_phy_set_port_en(uint8 lchip_id, uint32 gport,uint32 enable);
int32 ctc_phy_get_port_en(uint8 lchip_id, uint32 gport,uint32* enable);
int32 ctc_phy_set_port_duplex(uint8 lchip_id, uint32 gport,uint32 duplex);
int32 ctc_phy_get_port_duplex(uint8 lchip_id, uint32 gport,uint32* duplex);
int32 ctc_phy_set_port_speed(uint8 lchip_id, uint32 gport,uint32 speed);
int32 ctc_phy_get_port_speed(uint8 lchip_id, uint32 gport,uint32* speed);
int32 ctc_phy_set_port_auto_neg(uint8 lchip_id, uint32 gport,uint32 enable);
int32 ctc_phy_get_port_auto_neg(uint8 lchip_id, uint32 gport,uint32* enable);
int32 ctc_phy_set_port_loopback(uint8 lchip_id, uint32 gport,uint32 value);
int32 ctc_phy_get_port_loopback(uint8 lchip_id, uint32 gport,uint32* value);
int32 ctc_phy_get_link_up_status(uint8 lchip_id, uint32 gport,uint32* value);
int32 ctc_phy_set_port_unidir(uint8 lchip_id, uint32 gport,uint32 enable);
int32 ctc_phy_get_port_unidir(uint8 lchip_id, uint32 gport,uint32* enable);
int32 ctc_phy_set_port_medium(uint8 lchip_id, uint32 gport,uint32 value);
int32 ctc_phy_get_port_medium(uint8 lchip_id, uint32 gport,uint32* value);
int32 ctc_phy_set_port_ext_attr(uint8 lchip_id, uint32 gport,uint32 type, void* p_value);
int32 ctc_phy_get_port_ext_attr(uint8 lchip_id, uint32 gport,uint32 type, void* p_value);

int32 ctc_phy_driver_get_mars8p(void **drv);
int32 ctc_phy_driver_get_mars4c(void **drv);
int32 ctc_phy_driver_get_vsc8512(void **drv);
int32 ctc_phy_driver_get_mv88e1680(void **drv);
int32 ctc_phy_driver_get_rtl8218b(void **drv);
int32 ctc_phy_driver_get_mars1s(void **drv);

#endif /* !__PHY_API_H__ */
