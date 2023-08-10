/**
 @file ctc_chip.h

 @author  Copyright (C) 2011 Centec Networks Inc.  All rights reserved.

 @date 2009-11-30

 @version v2.0

   This file contains all chip related data structure, enum, macro and proto.
*/

#ifndef _CTC_CHIP_H
#define _CTC_CHIP_H
#ifdef __cplusplus
extern "C" {
#endif

/****************************************************************
 *
 * Header Files
 *
 ***************************************************************/

#include "ctc_mix.h"

/****************************************************************
*
* Defines and Macros
*
****************************************************************/

/****************************************************************
*
* Data Structures
*
****************************************************************/

/**
 @brief define chip type
*/
enum ctc_chip_type_e
{
    CTC_CHIP_NONE,              /**< [GB.GG]indicate this is a invalid chip */
    CTC_CHIP_GREATBELT,         /**< [GB]indicate this is a greatbelt chip */
    CTC_CHIP_GOLDENGATE,        /**< [GG]indicate this is a goldengate chip */
    CTC_CHIP_DUET2,             /**< [D2]indicate this is a duet2 chip */
    CTC_CHIP_TSINGMA,           /**< [TM]indicate this is a tsingma chip */
    MAX_CTC_CHIP_TYPE
};
typedef enum ctc_chip_type_e ctc_chip_type_t;

enum ctc_chip_mdio_type_e
{
    CTC_CHIP_MDIO_GE,                                   /**<[GB.GG.D2.TM] 1G phy */
    CTC_CHIP_MDIO_XG,                                   /**<[GB.GG.D2.TM] 10G phy */
    CTC_CHIP_MDIO_XGREG_BY_GE                   /**<[GB.GG] accecc 10 phy by 1G bus */
};
typedef enum ctc_chip_mdio_type_e ctc_chip_mdio_type_t;

struct ctc_chip_mdio_para_s
{
    uint8 ctl_id;                                                 /**<[GG] mdio slice id <0-1> */
    uint8 bus;                                                    /**<[GB.GG.D2.TM] bus id */
    uint8 phy_addr;                                            /**<[GB.GG.D2.TM] phy address */
    uint8 rsv;
    uint16 reg;                                                   /**<[GB.GG.D2.TM] register address */
    uint16 value;                                                /**<[GB.GG.D2.TM] config value */
    uint16 dev_no;                                              /**<[GB.GG.D2.TM] only usefull for xgphy */
    uint8 rsv1[2];
};
typedef struct ctc_chip_mdio_para_s ctc_chip_mdio_para_t;

struct ctc_phy_driver_s
{
  int32 (* init)(uint8 lchip, ctc_chip_mdio_para_t* param);
  int32 (* deinit)(uint8 lchip, ctc_chip_mdio_para_t* param);
  int32 (* set_port_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable);
  int32 (* get_port_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable);
  int32 (* set_port_duplex_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable);
  int32 (* get_port_duplex_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable);
  int32 (* set_port_speed)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 value);
  int32 (* get_port_speed)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_value);
  int32 (* set_port_auto_neg_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable);
  int32 (* get_port_auto_neg_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable);
  int32 (* set_port_loopback)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable);
  int32 (* get_port_loopback)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable);
  int32 (* get_link_up_status)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_link_up);
  int32 (* linkup_event)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* user_data);
  int32 (* linkdown_event)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* user_data);
  int32 (* set_port_unidir_en)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable);
  int32 (* get_port_unidir_en)(uint8 lchip, ctc_chip_mdio_para_t* param,  uint32* p_enable);
  int32 (* set_port_medium)(uint8 lchip, ctc_chip_mdio_para_t* param,  uint32 value);
  int32 (* get_port_medium)(uint8 lchip, ctc_chip_mdio_para_t* param,  uint32* p_value);
  int32 (* set_ext_attr)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value);
  int32 (* get_ext_attr)(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value);
};
typedef struct ctc_phy_driver_s ctc_phy_driver_t;

typedef int32 (*cust_ctc_mdio_write_f)(uint8 lchip, ctc_chip_mdio_type_t type, ctc_chip_mdio_para_t* p_para);
typedef int32 (*cust_ctc_mdio_read_f)(uint8 lchip, ctc_chip_mdio_type_t type, ctc_chip_mdio_para_t* p_para);

extern cust_ctc_mdio_write_f cust_ctc_mdio_write;
extern cust_ctc_mdio_read_f cust_ctc_mdio_read;
extern int32 ctc_phy_mdio_init(void);

#define CTC_CHIP_PHY_NAME_MAX_LEN 30
#define CTC_CHIP_PHY_MAX_IRQ_NUM 4
#define CTC_CHIP_PHY_NULL_PHY_ID 0xFFFFFFFFL

#ifdef __cplusplus
}
#endif

#endif
