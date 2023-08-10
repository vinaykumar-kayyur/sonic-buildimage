/**
 @file ctc_port.h

 @author  Copyright (C) 2011 Centec Networks Inc.  All rights reserved.

 @date 2011-11-9

 @version v2.0

 This file contains all port related data structure, enum, macro and proto.

*/

#ifndef _CTC_PORT_H
#define _CTC_PORT_H
#ifdef __cplusplus
extern "C" {
#endif

/****************************************************************
 *
 * Header Files
 *
 ***************************************************************/

#include "ctc_const.h"
/****************************************************************
*
* Defines and Macros
*
****************************************************************/

/**
 @defgroup port PORT
 @{
*/

/**
 @brief Port speed type
*/

enum ctc_port_speed_e
{
    CTC_PORT_SPEED_1G,          /**< [GB.GG.D2.TM] Port speed 1G mode*/
    CTC_PORT_SPEED_100M,        /**< [GB.GG.D2.TM] Port speed 100M mode*/
    CTC_PORT_SPEED_10M,         /**< [GB.GG.D2.TM] Port speed 10M mode*/
    CTC_PORT_SPEED_2G5,         /**< [GB.GG.D2.TM] Port speed 2.5G mode*/
    CTC_PORT_SPEED_10G,         /**< [GB.GG.D2.TM] Port speed 10G mode*/
    CTC_PORT_SPEED_20G,         /**< [GG.D2.TM] Port speed 20G mode*/
    CTC_PORT_SPEED_40G,         /**< [GG.D2.TM] Port speed 40G mode*/
    CTC_PORT_SPEED_100G,        /**< [GG.D2.TM] Port speed 100G mode*/
    CTC_PORT_SPEED_5G,          /**< [D2.TM] Port speed 5G mode*/
    CTC_PORT_SPEED_25G,         /**< [D2.TM] Port speed 25G mode*/
    CTC_PORT_SPEED_50G,         /**< [D2.TM] Port speed 50G mode*/
    CTC_PORT_SPEED_MAX
};
typedef enum ctc_port_speed_e ctc_port_speed_t;
/**
 @brief define mac type of port
*/
enum ctc_port_mac_type_e
{
    CTC_PORT_MAC_GMAC,      /**< [GB] mac type gmac, speed can be 1G 100M and 10M*/
    CTC_PORT_MAC_XGMAC,     /**< [GB] mac type Xgmac, speed at 10G*/
    CTC_PORT_MAC_SGMAC,     /**< [GB] mac type Sgmac, speed can be 13G*/
    CTC_PORT_MAC_CPUMAC,    /**< [GB] mac type Cpumac, uplink to cpu*/
    CTC_PORT_MAC_MAX
};
typedef enum ctc_port_mac_type_e ctc_port_mac_type_t;

enum ctc_port_fec_type_e
{
    CTC_PORT_FEC_TYPE_NONE,          /**< [D2.TM] FEC OFF, if set, #1)FEC config will ALL be clear
                                                                #2)CL73 Auto-Neg will NOT negotiate FEC abilty */
    CTC_PORT_FEC_TYPE_RS,            /**< [D2.TM] RS FEC, if set, RS FEC config will be set */
    CTC_PORT_FEC_TYPE_BASER,         /**< [D2.TM] BASE-R FEC, if set, BASE-R FEC config will be set */
    CTC_PORT_FEC_TYPE_MAX
};
typedef enum ctc_port_fec_type_e ctc_port_fec_type_t;
enum ctc_port_auto_neg_mode_e
{
    CTC_PORT_AUTO_NEG_MODE_1000BASE_X,             /**< [GB.GG.D2.TM] 1000BASE-X Auto-neg mode */
    CTC_PORT_AUTO_NEG_MODE_SGMII_MASTER,          /**< [GB.GG.D2.TM] SGMII master Auto-neg mode */
    CTC_PORT_AUTO_NEG_MODE_SGMII_SLAVER,          /**< [GB.GG.D2.TM] SGMII slaver Auto-neg mode */
    CTC_PORT_AUTO_NEG_MODE_MAX_MODE
};
typedef enum ctc_port_auto_neg_mode_e ctc_port_auto_neg_mode_t;

/**
  @brief Port property flags
*/
enum ctc_port_property_e
{
    CTC_PORT_PROP_SPEED,                                  /**< [GB.GG.D2.TM] port speed*/
    CTC_PORT_PROP_UNIDIR_EN,                       /**< [GB.GG.D2.TM] Enable fiber unidirection */

    /* Phy property*/
    CTC_PORT_PROP_PHY_INIT,                 /**< [D2.TM] phy port init*/
    CTC_PORT_PROP_PHY_EN,                   /**< [D2.TM] phy port enable*/
    CTC_PORT_PROP_PHY_DUPLEX,               /**< [D2.TM] phy duplext*/
    CTC_PORT_PROP_PHY_MEDIUM,               /**< [D2.TM] phy medium*/
    CTC_PORT_PROP_PHY_LOOPBACK,             /**< [D2.TM] phy loopback*/
    CTC_PORT_PROP_PHY_AUTO_NEG_EN,          /**< [D2.TM] phy auto neg enable*/
    CTC_PORT_PROP_PHY_CUSTOM_BASE = 2000,
    CTC_PORT_PROP_PHY_CUSTOM_MAX_TYPE = 2100,

    MAX_CTC_PORT_PROP_NUM
};
typedef enum ctc_port_property_e  ctc_port_property_t;

/**
 @brief Port interface type
*/
enum ctc_port_if_type_e
{
    CTC_PORT_IF_NONE = 0,      /**< [D2.TM] Invalid interface type */
    CTC_PORT_IF_SGMII,         /**< [D2.TM] SGMII type */
    CTC_PORT_IF_2500X,         /**< [D2.TM] 2500X type */
    CTC_PORT_IF_QSGMII,        /**< [D2.TM] QSGMII type */
    CTC_PORT_IF_USXGMII_S,     /**< [D2.TM] USXGMII Single type */
    CTC_PORT_IF_USXGMII_M2G5,  /**< [D2.TM] USXGMII Multi 2.5G type */
    CTC_PORT_IF_USXGMII_M5G,   /**< [D2.TM] USXGMII Multi 5G type */
    CTC_PORT_IF_XAUI,          /**< [D2.TM] XAUI type */
    CTC_PORT_IF_DXAUI,         /**< [D2.TM] DXAUI type */
    CTC_PORT_IF_XFI,           /**< [D2.TM] XFI type */
    CTC_PORT_IF_KR,            /**< [D2.TM] KR type, 1 lane per port */
    CTC_PORT_IF_CR,            /**< [D2.TM] CR type, 1 lane per port */
    CTC_PORT_IF_KR2,           /**< [D2.TM] KR2 type, 2 lanes per port */
    CTC_PORT_IF_CR2,           /**< [D2.TM] CR2 type, 2 lanes per port */
    CTC_PORT_IF_KR4,           /**< [D2.TM] KR4 type, 4 lanes per port */
    CTC_PORT_IF_CR4,           /**< [D2.TM] CR4 type, 4 lanes per port */
    CTC_PORT_IF_FX,            /**< [TM] 100BaseFX */

    CTC_PORT_IF_MAX_TYPE
};
typedef enum ctc_port_if_type_e ctc_port_if_type_t;

#ifdef __cplusplus
}
#endif

#endif
