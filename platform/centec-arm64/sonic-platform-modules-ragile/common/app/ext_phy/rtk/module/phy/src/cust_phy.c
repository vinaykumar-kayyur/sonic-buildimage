#include <rtk/phy.h>
#include <phy_init.h>
#include <common/rt_type.h>
#include <common/rt_error.h>
#include <common/debug/rt_log.h>
#include <string.h>
#include <dlfcn.h>
#include <pthread.h>
#include <time.h>
#include <stdbool.h>

#define PHY_MAX_PARAMS           16
#define PHY_PARAM_SPLIT          ","
#define PHY_MAX_PARAMS_CHAR      256

#define PHY_ID_MASK                 0xffffffff
#define PHY_NAME_RTL8218D           "rtl8218d"
#define PHY_NAME_RTL8214FC          "rtl8214fc"
#define PHY_TYPE_RTL8218D           0x001cc983
#define PHY_TYPE_RTL8214FC          0x001cc981

#define PHY_NAME_RTL8218E           "rtl8218e"
#define PHY_TYPE_RTL8218E           0x001cc984

#define CTC_CHIP_PHY_NAME_MAX_LEN 30
#define CTC_CHIP_PHY_MAX_IRQ_NUM 4

#define CTCSDK_CHIP_PROP_SET_SYMBOL    "ctcs_chip_set_property"
#define CTCSDK_PORT_SPEED_SET_SYMBOL   "ctcs_port_set_speed"
#define CTCSDK_PORT_PROP_SET_SYMBOL   "ctcs_port_set_property"

#define MAX_PORT_NUM    64

pthread_mutex_t speed_update_pending_mutex[MAX_PORT_NUM];
bool speed_update_flag[MAX_PORT_NUM];
extern phy_hwp_portDescp_t cust_port_descp_48e4x[];

uint32 page_rw_g;
bool ctc_port_autoneg_off;

extern int32 dev_autoneg_off_g;

enum ctc_port_phy_attr_e
{
    CTC_PORT_PROP_PHY_HELP_INFO = 2000,
    CTC_PORT_PROP_PHY_EYEPARAM_AMP,
    CTC_PORT_PROP_PHY_SPEED,
    CTC_PORT_PROP_PHY_REG_PAGE = 2098,
    CTC_PORT_PROP_PHY_REG_READ = 2099,
    CTC_PORT_PROP_PHY_REG_WRITE = 2100, /* 2000-2100 is valid */
};

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

struct ctc_chip_phy_shim_s
{
    uint32 phy_id;                              /**< [D2.TM] 32bit phy id */
    uint32 phy_id_mask;                         /**< [D2.TM] 32bit phy id mask */
    char phy_name[CTC_CHIP_PHY_NAME_MAX_LEN];   /**< [D2.TM] Phy Name */
    ctc_phy_driver_t driver;                    /**< [D2.TM] the driver for this phy */
    void *user_data;                            /**< [D2.TM] user_data for callback function param.  */
    uint32 event_mode;                          /**< [D2.TM] linkup or linkdown event mode. refer to ctc_chip_phy_shim_event_mode_t */
    uint16 irq[CTC_CHIP_PHY_MAX_IRQ_NUM];       /**< [D2.TM] user_data for callback function param. the irq must not zero */
    uint16 poll_interval;                       /**< [D2.TM] poll interval time, equal zero: disable, other:enable-unit: ms*/
};
typedef struct ctc_chip_phy_shim_s ctc_chip_phy_shim_t;

enum ctc_chip_phy_shim_event_mode_e
{
    CTC_CHIP_PHY_SHIM_EVENT_MODE_SCAN,      /**<[D2.TM] get phy port link up/down, by mdio scan */
    CTC_CHIP_PHY_SHIM_EVENT_MODE_IRQ,       /**<[D2.TM] get phy port link up/down, by irq */
    CTC_CHIP_PHY_SHIM_EVENT_MODE_POLLING,   /**<[D2.TM] get phy port link up/down, by polling */
    CTC_CHIP_PHY_SHIM_MAX_EVENT_MODE
};
typedef enum ctc_chip_phy_shim_event_mode_e ctc_chip_phy_shim_event_mode_t;

enum ctc_chip_property_e
{
    CTC_CHIP_PROP_SERDES_FFE,               /**<[GB.GG.D2.TM] config serdes ffe parameter, refer to ctc_chip_serdes_ffe_t */
    CTC_CHIP_PEOP_SERDES_POLARITY,      /**<[GG.D2.TM] config serdes polarity */
    CTC_CHIP_PROP_SERDES_PRBS,             /**<[GB.GG.D2.TM] config serdes prbs */
    CTC_CHIP_PROP_SERDES_LOOPBACK,     /**<[GB.GG.D2.TM] config serdes loopback */
    CTC_CHIP_PROP_SERDES_P_FLAG,   /**<[GG.D2.TM] when optical using Pre-emphasis mode, for trace length
                                                 too short serdes, need config this mode to reduce p-flag
                                                 value: 0:disable, 1:enable */
    CTC_CHIP_PROP_SERDES_PEAK,         /**<[GB.GG.D2.TM] peaking value, when dpc is 1, the peak is invalid. refer to ctc_chip_serdes_cfg_t
                                                   value: HSS28G:0-31 other:0-7 */
    CTC_CHIP_PROP_SERDES_DPC,          /**<[GB.GG.D2.TM] enable or disable dynamic Peaking Control, refer to ctc_chip_serdes_cfg_t
                                                   value: 0:disable, 1:enable */
    CTC_CHIP_PROP_SERDES_SLEW_RATE,    /**<[GB.GG.D2.TM] config serdes slew rate, refert to ctc_chip_serdes_cfg_t,
                                                   value: [GB]  0:>4.5Gbps 1:3.126-4.25Gbps 2:<3.126Gbps
                                                          [GG]  HSS28G 0:full rate 1:10G
                                                                HSS15G 0:full rate 1:full rate for 802.3ap kr
                                                                       2:medium 3:slow */

    CTC_CHIP_PROP_EEE_EN,                       /**<[GB.GG.D2.TM] enable eee globally */
    CTC_CHIP_PROP_SERDES_ID_TO_GPORT,           /**<[GB.GG.D2.TM] get gport with serdes_id, refer to ctc_port_serdes_info_t */
    CTC_CHIP_PHY_SCAN_EN,                       /**<[GB.D2.TM] enable phy scan */
    CTC_CHIP_PHY_SCAN_PARA,                     /**<[D2.TM] set phy scan para, refer to ctc_chip_phy_scan_ctrl_t */
    CTC_CHIP_I2C_SCAN_EN,                       /**<[GB.D2.TM] enable I2C Master scan */
    CTC_CHIP_I2C_SCAN_PARA,                     /**<[D2.TM] set i2c scan para, refer to ctc_chip_i2c_scan_t */
    CTC_CHIP_MAC_LED_EN,                        /**<[GB.GG.D2.TM] enable Mac Led */
    CTC_CHIP_PROP_MEM_SCAN,                     /**<[GG.D2.TM] enable tcam key and single bit error scan */
    CTC_CHIP_PROP_GPIO_MODE,                    /**<[GB.GG.D2.TM] set GPIO working mode ctc_chip_gpio_mode_t */
    CTC_CHIP_PROP_GPIO_OUT,                     /**<[GB.GG.D2.TM] write Value onto the GPIO with ctc_chip_gpio_params_t */
    CTC_CHIP_PROP_GPIO_IN,                      /**<[GB.GG.D2.TM] read Value from the GPIO with ctc_chip_gpio_params_t */
    CTC_CHIP_PROP_GPIO_CFG,                     /**<[TM] set GPIO config with ctc_chip_gpio_cfg_t */
    CTC_CHIP_PROP_PHY_MAPPING,                  /**<[GB.GG.D2.TM] set mdio and phy mapping relation, Value is a pointer to ctc_chip_phy_mapping_para_t */

    CTC_CHIP_PROP_DEVICE_INFO,                  /**<[GB.GG.D2.TM] chip device information */
    CTC_CHIP_PROP_MEM_BIST,                     /**<[GB.GG.D2.TM] memory BIST, Value is a pointer to ctc_chip_mem_bist_t, GB will take a few seconds */
    CTC_CHIP_PROP_RESET_HW,                     /**<[D2.TM] Reset chip hardware,recover chip data*/
    CTC_CHIP_PROP_PERI_CLOCK,                   /**<[TM] set peri clock, refer to ctc_chip_peri_clock_t */
    CTC_CHIP_PROP_MAC_LED_BLINK_INTERVAL,       /**<[D2.TM] set Mac Led blink interval,  time cycle(ns) = 1000*interval/coreclock(MHZ) default 0x0d1cef00*/
    CTC_CHIP_PROP_SERDES_CTLE,                  /**<[TM] changle ctle ,  refer to ctc_chip_serdes_ctle_t */
    CTC_CHIP_PROP_REGISTER_PHY,                 /**<[D2.TM] phy regiseter,  refer to ctc_chip_phy_shim_t*/
    CTC_CHIP_PROP_CPU_PORT_EN,                  /**<[GG.D2.TM] cpu port enable, refer to ctc_chip_cpu_port_t*/
    CTC_CHIP_PROP_SERDES_DFE,                   /**<[TM]config serdes DFE enable or disable, refer to ctc_chip_serdes_cfg_t*/
    CTC_CHIP_PROP_SERDES_EYE_DIAGRAM,           /**<[TM][out] get serdes eye diagram parameter, refer to ctc_chip_serdes_eye_diagram_t*/
    CTC_CHIP_PROP_MAX_TYPE
};
typedef enum ctc_chip_property_e ctc_chip_property_t;

enum ctc_port_property_e
{
    /**< genernal property */
    CTC_PORT_PROP_MAC_EN,                         /**< [GB.GG.D2.TM] Port mac enable*/
    CTC_PORT_PROP_PORT_EN,                        /**< [GB.GG.D2.TM] Port whether the port is enable,
                                                                            the following properties will be set:
                                                                            CTC_PORT_PROP_TRANSMIT_EN,
                                                                            CTC_PORT_PROP_RECEIVE_EN and CTC_PORT_PROP_BRIDGE_EN*/
    CTC_PORT_PROP_LINK_UP,                        /*<  [GB.GG.D2.TM] Port link up status */
    CTC_PORT_PROP_VLAN_CTL,                      /**< [GB.GG.D2.TM] Port's vlan tag control mode*/
    CTC_PORT_PROP_DEFAULT_VLAN,              /**< [GB.GG.D2.TM] Default vlan id, the following properties will be set:
                                                                           untag_default_svlan = 1,untag_default_vlanId = 1,
                                                                           DsPhyPortExt_DefaultVlanId_f and DsDestPort_DefaultVlanId_f*/
    CTC_PORT_PROP_UNTAG_PVID_TYPE,         /**< [GB.GG.D2.TM] Untag default vlan type. refer CTC_PORT_UNTAG_PVID_TYPE_XXX */
    CTC_PORT_PROP_VLAN_DOMAIN,               /**< [GB.GG.D2.TM] vlan domain of the port */

    CTC_PORT_PROP_PROTOCOL_VLAN_EN,               /**< [GB.GG.D2.TM] protocol vlan enable*/
    CTC_PORT_PROP_QOS_POLICY,                          /**< [GB.GG.D2.TM] QOS policy*/
    CTC_PORT_PROP_DEFAULT_PCP,                         /**< [GB.GG.D2.TM] default PCP*/
    CTC_PORT_PROP_DEFAULT_DEI,                         /**< [GB.GG.D2.TM] default DEI*/
    CTC_PORT_PROP_SCL_USE_DEFAULT_LOOKUP,    /**< [GB.GG.D2.TM] SCL default vlan lookup*/
    CTC_PORT_PROP_SCL_IPV4_LOOKUP_EN,            /**< [GB] SCL ipv4 lookup enable*/
    CTC_PORT_PROP_SCL_IPV6_LOOKUP_EN,            /**< [GB] SCL ipv6 lookup enable*/
    CTC_PORT_PROP_SCL_FORCE_IPV4_TO_MAC,      /**< [GB] force Ipv4 packet go against MAC SCL entry*/
    CTC_PORT_PROP_SCL_FORCE_IPV6_TO_MAC,      /**< [GB] force Ipv6 packet go against MAC SCL entry*/
    CTC_PORT_PROP_NVGRE_MCAST_NO_DECAP,      /**< [GG.D2.TM] NvGRE mcast packet do not decapsulation*/
    CTC_PORT_PROP_VXLAN_MCAST_NO_DECAP,      /**< [GG.D2.TM] VxLAN mcast packet do not decapsulation*/
    CTC_PORT_PROP_PTP_EN,                        /**< [GB.GG.D2.TM] set ptp clock id, refer to ctc_ptp_clock_t */

    CTC_PORT_PROP_SPEED,                                  /**< [GB.GG.D2.TM] port speed*/
    CTC_PORT_PROP_MAX_FRAME_SIZE,                 /**< [GB.GG.D2.TM] max frame size*/
    CTC_PORT_PROP_MIN_FRAME_SIZE,                 /**< [GB.GG.D2.TM] min frame size*/
    CTC_PORT_PROP_PREAMBLE,                           /**< [GB.GG.D2.TM] preamble value*/
    CTC_PORT_PROP_PADING_EN,                          /**< [GB.GG.D2.TM] pading enable*/
    CTC_PORT_PROP_STRETCH_MODE_EN,              /**< [GB] port stretch mode enable*/
    CTC_PORT_PROP_IPG,                                     /**< [GB.GG.D2.TM] ipg index per port*/
    CTC_PORT_PROP_RX_PAUSE_TYPE,                  /**< [GB.GG] set port rx pause type, normal or pfc*/
    CTC_PORT_PROP_MAC_TS_EN,                         /**< [GB] Enable Mac for append time-stamp */
    CTC_PORT_PROP_ERROR_CHECK,                     /**< [GB.GG.D2.TM] Mac CRC check, 1:enable, 0:disable */
    CTC_PORT_PROP_MAC_TX_IPG,                       /**< [GB.GG.D2.TM] mac tx ipg size, the value must be 8bytes or 12bytes(default) */
    CTC_PORT_PROP_OVERSUB_PRI,                     /**< [GG.D2.TM] Oversubscription port bandwidth guarantee priority, oversubscription allows ingress ports bandwidth
                                                                                greater than the core bandwidth of the device and per port set bandwidth guarantee priority, for GG: 0-low,1-high, Default is 0 */
    CTC_PORT_PROP_TRANSMIT_EN,                    /**< [GB.GG.D2.TM] Tx enable*/
    CTC_PORT_PROP_RECEIVE_EN,                      /**< [GB.GG.D2.TM] Rx enable*/
    CTC_PORT_PROP_BRIDGE_EN,                       /**< [GB.GG.D2.TM] bridge enable in both direction*/
    CTC_PORT_PROP_LEARNING_EN,                    /**< [GB.GG.D2.TM] learning enable*/
    CTC_PORT_PROP_PRIORITY_TAG_EN,             /**< [GB.GG.D2.TM] priority tag enable*/

    CTC_PORT_PROP_CROSS_CONNECT_EN,               /**< [GB.GG.D2.TM] port cross connect*/
    CTC_PORT_PROP_DOT1Q_TYPE,                           /**< [GB.GG.D2.TM] dot1q type*/
    CTC_PORT_PROP_USE_OUTER_TTL,                       /**< [GB.GG.D2.TM] use outer ttl in case of tunnel*/
    CTC_PORT_PROP_DISCARD_NON_TRIL_PKT,          /**< [GB.GG.D2.TM] discard non-trill pkg enable*/
    CTC_PORT_PROP_DISCARD_TRIL_PKT,                  /**< [GB.GG.D2.TM] discard trill pkg enable*/
    CTC_PORT_PROP_SRC_DISCARD_EN,                    /**< [GB.GG.D2.TM] port whether the srcdiscard is enable*/
    CTC_PORT_PROP_PORT_CHECK_EN,                     /**< [GB.GG.D2.TM] port port check enable*/
    CTC_PORT_PROP_RAW_PKT_TYPE,                       /**< [GB.GG.D2.TM] raw packet type*/

    CTC_PORT_PROP_REFLECTIVE_BRIDGE_EN,           /**< [GB.GG.D2.TM] bridge to the same port enable*/
    CTC_PORT_PROP_HW_LEARN_EN,                         /**< [GB.GG.D2.TM] hw learning enable*/
    CTC_PORT_PROP_TRILL_EN,                                 /**< [GB.GG.D2.TM] trill enable*/
    CTC_PORT_PROP_TRILL_MCAST_DECAP_EN,           /**< [GG.D2.TM] trill mcast decap when enable*/
    CTC_PORT_PROP_FCOE_EN,                                  /**< [GB.GG.D2.TM] FCOE enable*/
    CTC_PORT_PROP_RPF_EN,                                    /**< [GB.GG.D2.TM] RPF enable*/
    CTC_PORT_PROP_FCMAP,                                     /**< [GG.D2.TM] fcoe FCMAP(0x0EFC00-0x0EFCFF), default is 0x0EFC00 */
    CTC_PORT_PROP_REPLACE_STAG_COS,                 /**< [GB.GG.D2.TM] the STAG COS field is replaced by the classified COS result*/
    CTC_PORT_PROP_REPLACE_STAG_TPID,                /**< [GG.D2.TM] the STAG TPID is replaced by the vlanXlate TPID result*/
    CTC_PORT_PROP_REPLACE_CTAG_COS,                /**< [GB.GG.D2.TM] the STAG COS field is replaced by the classified COS result*/
    CTC_PORT_PROP_REPLACE_DSCP_EN,                  /**< [GB.GG.D2.TM] the dscp field is replaced by the classified qos result, D2 replaced by CTC_PORT_PROP_DSCP_SELECT_MODE*/

    CTC_PORT_PROP_L3PDU_ARP_ACTION,                /**< [GB.GG.D2.TM] l3PDU arp action*/
    CTC_PORT_PROP_L3PDU_DHCP_ACTION,             /**< [GB.GG.D2.TM] l3PDU dhcp action*/
    CTC_PORT_PROP_L3PDU_DHCP_V6_ACTION,          /**< [D2.TM.TMM] l3PDU dhcp v6 action*/
    CTC_PORT_PROP_TUNNEL_RPF_CHECK,               /**< [GB.GG.D2.TM] tunnel RPF check enable*/
    CTC_PORT_PROP_RPF_TYPE,                              /**< [GB.GG.D2.TM] RPF type, refer to ctc_port_rpf_type_t */
    CTC_PORT_PROP_IS_LEAF,                                /**< [GB.GG.D2.TM] the port connect with a leaf node*/
    CTC_PORT_PROP_PKT_TAG_HIGH_PRIORITY,       /**< [GB.GG.D2.TM] Packet tag take precedence over all*/
    CTC_PORT_PROP_ROUTE_EN,                             /**< [GB.GG.D2.TM] Enable route on port */

    CTC_PORT_PROP_AUTO_NEG_EN,                       /**< [GB.GG.D2.TM] Enable Auto-neg on port */
    CTC_PORT_PROP_AUTO_NEG_MODE,                  /**< [GB.GG.D2.TM] Config Auto-neg mode on port */
    CTC_PORT_PROP_CL73_ABILITY,                       /**< [GG.D2.TM] cfg cl73 ability */
    CTC_PORT_PROP_FEC_EN,                                /**< [GG.D2.TM] Enable FEC, mac must be disable */
    CTC_PORT_PROP_LINK_INTRRUPT_EN,                /**< [GB.GG.D2.TM] Enable Mac PCS link interrupt */
    CTC_PORT_PROP_UNIDIR_EN,                       /**< [GB.GG.D2.TM] Enable fiber unidirection */
    CTC_PORT_PROP_CUT_THROUGH_EN,                  /**< [GG.D2.TM] enable cut through */
    CTC_PORT_PROP_PAR_DET_EN,                      /**< [TM] parallel detection enable */

    CTC_PORT_PROP_LINKSCAN_EN,                       /**< [GB.GG.D2.TM] Enable linkscan funciton on port*/
    CTC_PORT_PROP_APS_FAILOVER_EN,                /**< [GB.GG.D2.TM] Enable Aps-failover on port*/
    CTC_PORT_PROP_LINKAGG_FAILOVER_EN,         /**< [GB.GG.D2.TM] Enable Linkagg-failover on port*/
    CTC_PORT_PROP_SCL_HASH_FIELD_SEL_ID,     /**< [GG.D2.TM] SCL flow hash field sel id */
    CTC_PORT_PROP_APS_SELECT_GRP_ID,            /**< [GG.D2.TM] The aps select group id, 0xFFFFFFFF means disable aps select*/
    CTC_PORT_PROP_APS_SELECT_WORKING,         /**< [GG.D2.TM] Indicate the flow is working path or protecting path*/

    CTC_PORT_PROP_SNOOPING_PARSER,                         /**< [GG.D2.TM] Enable parser tunnel payload even no tunnel decap */
    CTC_PORT_PROP_FLOW_LKUP_BY_OUTER_HEAD,         /**< [GG.D2.TM] If set,indicate tunnel packet will use outer header to do ACL/IPFIX flow lookup */
    CTC_PORT_PROP_AWARE_TUNNEL_INFO_EN,            /**< [GG.D2.TM] If set, indicate use pkt inner info as lookup key, and outer l4 info can also be used as lookup key */
    CTC_PORT_PROP_NVGRE_ENABLE,                   /**< [GG.D2.TM] Enable nvgre */

    CTC_PORT_PROP_METADATA_OVERWRITE_PORT,        /**< [GG.D2.TM] Enable metadata overwrite port */
    CTC_PORT_PROP_METADATA_OVERWRITE_UDF,         /**< [GG] Enable metadata overwrite udf */

    CTC_PORT_PROP_SIGNAL_DETECT,                            /**< [GG.D2.TM] Signal detect on port */

    CTC_PORT_PROP_SRC_MISMATCH_EXCEPTION_EN,      /**< [GB.GG.D2.TM] Enable station move to cpu */
    CTC_PORT_PROP_STATION_MOVE_PRIORITY,               /**< [GB.GG.D2.TM] Station move priority: 0-low,1-high, Default is 0 */
    CTC_PORT_PROP_STATION_MOVE_ACTION,                  /**< [GB.GG.D2.TM] Station move action, refer to ctc_port_station_move_action_type_t */
    CTC_PORT_PROP_EFD_EN,                                          /**< [GG.D2.TM] Enable EFD */
    CTC_PORT_PROP_EEE_EN,                                          /**< [GB.GG.D2.TM] Enable eee on port*/

    CTC_PORT_PROP_LOGIC_PORT,                     /**< [GB.GG.D2.TM] Port logic port value. if set 0, mean logic port disable */
    CTC_PORT_PROP_GPORT,                     /**< [D2.TM] Set port gport value. */
    CTC_PORT_PROP_ADD_DEFAULT_VLAN_DIS,           /**< [GB.GG.D2.TM] Will not add default vlan for untagged packet */
    CTC_PORT_PROP_IPFIX_LKUP_BY_OUTER_HEAD,         /**< [D2.TM] If set,indicate tunnel packet will use outer header to do IPFIX flow lookup */
    CTC_PORT_PROP_IPFIX_AWARE_TUNNEL_INFO_EN,     /**< [D2.TM] If set, indicate ipfix lookup key use innner info as key, and outer tunnel info can also be used as lookup key */
    CTC_PORT_PROP_CID,                            /**< [D2.TM] Category Id*/
    CTC_PORT_PROP_TX_CID_HDR_EN,                  /**< [D2.TM] Tx Packet with cid header.*/
    CTC_PORT_PROP_WLAN_PORT_TYPE,                 /**< [D2.TM] WLAN port type, refer to ctc_port_wlan_port_type_t */
    CTC_PORT_PROP_WLAN_PORT_ROUTE_EN,             /**< [D2.TM] Enable inner packet route on the wlan port */
    CTC_PORT_PROP_WLAN_DECAP_WITH_RID,            /**< [D2.TM] If not zero means radio id used as key of WLAN decap */
    CTC_PORT_PROP_DSCP_SELECT_MODE,               /**< [D2.TM] [Egress]Dscp select mode, refer to ctc_dscp_select_mode_t */
    CTC_PORT_PROP_DEFAULT_DSCP,                   /**< [D2.TM] [Egress]Default DSCP, if DSCP_SELECT_MODE is CTC_DSCP_SELECT_ASSIGN, the default dscp will rewrite packet's dscp */
    CTC_PORT_PROP_REPLACE_PCP_DEI,                /**< [D2.TM] [Egress]The classified PCP/DEI is replaced by the Default PCP/DEI */
    CTC_PORT_PROP_LOGIC_PORT_CHECK_EN,            /**< [D2.TM] [Egress]Port logic port check enable */
    CTC_PORT_PROP_LOOP_WITH_SRC_PORT,             /**< [GG.D2.TM] if set, indicate the loop packet will take source port back, or used for taking source port to CPU */

    CTC_PORT_PROP_BPE_PORT_TYPE,                  /**< [D2.TM] BPE(Bridge port extend) port type, refer to ctc_port_bpe_extend_type_t*/
    CTC_PORT_PROP_BPE_NAMESPACE,                  /**< [D2.TM] BPE port namespace which is used to differentiate same extend vlan*/
    CTC_PORT_PROP_BPE_EXTEND_VLAN,                /**< [D2.TM] BPE extend vlan*/
    CTC_PORT_PROP_SD_ACTION,                      /**< [D2.TM] Port enable Singal Degrade, refer to ctc_port_sd_action_type_t*/

    CTC_PORT_PROP_LB_HASH_ECMP_PROFILE,           /**< [TM] Port sel hash offset profile id for ecmp or packet head, refer to ctc_lb_hash_offset_t*/
    CTC_PORT_PROP_LB_HASH_LAG_PROFILE,            /**< [TM] Port sel hash offset profile id for linkagg, refer to ctc_lb_hash_offset_t*/
    CTC_PORT_PROP_LB_HASH_VALUE,                  /**< [TM.TM2] Port lb-hash value, only use for stacking*/

    CTC_PORT_PROP_LEARN_DIS_MODE,                 /**< [TM] Learn disable mode: 1-learn disable with mac sa lookup, 0-learn disable with no mac sa lookup */
    CTC_PORT_PROP_FORCE_MPLS_EN,                  /**< [TM] Force MPLS packet decap */
    CTC_PORT_PROP_FORCE_TUNNEL_EN,                /**< [TM] Force Tunnel packet decap */
    CTC_PORT_PROP_DISCARD_UNENCRYPT_PKT,          /**< [TM] Discard unencrypted packet, except for some special packets */
    CTC_PORT_PROP_XPIPE_EN,                       /**< [TM] Enable/disable XPIPE feature */
    CTC_PORT_PROP_QOS_WRR_EN,                     /**< [D2.TM] Enable/disable WRR mode*/
    CTC_PORT_PROP_ESID,                            /**< [TM] Evpn EsId*/
    CTC_PORT_PROP_ESLB,                            /**< [TM] Evpn EsLabel*/
    /* Mac Property */
    CTC_PORT_PROP_CHK_CRC_EN = 1000,              /**< [D2.TM] packet check RX CRC Enable*/
    CTC_PORT_PROP_STRIP_CRC_EN,                   /**< [D2.TM] packet strip TX CRC Enable*/
    CTC_PORT_PROP_APPEND_CRC_EN,                  /**< [D2.TM] packet append TX CRC Enable*/
    CTC_PORT_PROP_APPEND_TOD_EN,                  /**< [D2.TM] packet append RX tod Enable*/

    CTC_PORT_PROP_AUTO_NEG_FEC,                   /**< [D2.TM] Config Auto-neg FEC ability on port, refer to 'ctc_port_fec_type_t'
                                                            set value 0 -- disable Auto-Neg FEC ability;
                                                            set value 1 -- enable Auto-Neg FEC RS type ability;
                                                            set value 2 -- enable Auto-Neg FEC Base-R type ability;
                                                            set other value -- return error */
    CTC_PORT_PROP_INBAND_CPU_TRAFFIC_EN,          /**< [D2.TM] Set port inband CPU traffic enable, only used for WDM Pon*/
    CTC_PORT_PROP_MUX_TYPE,                       /**< [GG.D2.TM] Set packet encap format for ingress port identify, refer to ctc_port_mux_type_t */
    CTC_PORT_PROP_STK_GRP_ID,                     /**< [D2.TM] Config stacking trunk select group id for ucast path select when select_mode == 1 */
    CTC_PORT_PROP_FEC_CNT,                        /**< [TM] [out] FEC count, refer to ctc_port_fec_cnt_t*/
    CTC_PORT_PROP_SFD_EN,                         /**< [D2.TM] disable: 0x5d(sfd) centec mode, use for centec stacking ports interconnect,
                                                               enable: 0xd5(sfd) normal mode, use for normal ports interconnect(default)*/
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

typedef int32 (*ctcs_chip_set_property_f)(uint8 lchip, ctc_chip_property_t chip_prop, void* p_value);

typedef int32 (*ctcs_port_set_speed_f)(uint8 lchip, uint32 gport, ctc_port_speed_t speed_mode);
typedef int32 (*ctcs_port_set_property_f)(uint8 lchip, uint32 gport, ctc_port_property_t port_prop, uint32 value);

extern int cust_rtk_mdio_read(int unit, int port, int page, uint32 reg, uint32 *val);
extern int cust_rtk_mdio_write(int unit, int port, int page, uint32 reg, uint32 val);

ctcs_port_set_property_f cust_ctcs_port_set_property;
ctcs_port_set_speed_f cust_ctcs_port_set_speed;

static int c2int(char *str, int *val)
{
    int base = 0;
    if (val) {
        if (*str == '0') {
            if (str[1] == 'b' || str[1] == 'B') {
                base = 2;
                str += 2;
            } else if (str[1] == 'x' || str[1] == 'X') {
                base = 16;
                str += 2;
            } else
                base = 8;
        } else {
            base = 10;
        }
        *val = (int)strtol(str, NULL, base);
    }
    return 0;
}

int32 parse_rtk_port(uint32 port)
{
    uint32 ctc_port;

    /* cur only for 48e device */
    if (port >= 12 && port <= 15) {
        ctc_port = port + 32 - 12;
    } else if (port >= 28 && port <= 31) {
        ctc_port = port + 48 - 28;
    } else {
        ctc_port = port;
    }

    return ctc_port;
}

int32 cust_extphy_rtk_init(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    int32 rv;
    uint32 unit, port;

    unit = lchip;
    rv =  cust_rtk_init(unit);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d init fail, rv:%d\n", unit, rv);
        return rv;
    }
    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d init success\n", unit, port);

    return rv;
}

int32 cust_extphy_rtk_deinit(uint8 lchip, ctc_chip_mdio_para_t* param)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d deinit not support\n", unit, port);
    return RT_ERR_OK;
}

int32 cust_extphy_rtk_set_port_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    rv =  rtk_port_adminEnable_set(unit, port, enable);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d en:%d set fail, rv:%d\n", unit, port, enable, rv);
    } else {
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d en:%d set success\n", unit, port, enable);
    }

    return rv;
}

int32 cust_extphy_rtk_get_port_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    /* rtk api not support, 0: To prevent non setting during sai start-up */
    *p_enable = 0;

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d en:%d get not support\n", unit, port, *p_enable);
    return RT_ERR_OK;
}

int32 cust_extphy_rtk_set_port_duplex_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d duplex_en:%d set not support\n", unit, port, enable);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_get_port_duplex_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    *p_enable = 1;

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d duplex_en:%d get not support\n", unit, port, *p_enable);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_get_link_up_status(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_link_up)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        *p_link_up = 0;
        return RT_ERR_OK;
    }

    rv =  rtk_port_phyLinkStatus_get(unit, port, p_link_up);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d link get fail, rv:%d\n", unit, port, rv);
        *p_link_up = 0;
    } else {
        /* too frequently
         * CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d link:%d get success\n", unit, port, *p_link_up);
         */
    }

    return rv;
}

int32 cust_extphy_rtk_set_port_speed(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 value)
{
    int32 rv;
    uint32 unit, port;
    rtk_port_speed_t rtk_speed;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    /* from ctc speed type */
    switch (value) {
    case CTC_PORT_SPEED_1G:
        rtk_speed = PORT_SPEED_1000M;
        break;
    case CTC_PORT_SPEED_100M:
        rtk_speed = PORT_SPEED_100M;
        break;
    case CTC_PORT_SPEED_10M:
        rtk_speed = PORT_SPEED_10M;
        break;
    default:
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d invalid speed:%d\n", unit, port, value);
        return RT_ERR_FAILED;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d speed:%d rtk_speed:%d set not support\n", unit, port, value, rtk_speed);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_get_port_speed(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_value)
{
    int32 rv;
    uint32 unit, port;
    uint32 link_sta;
    rtk_port_duplex_t duplex;
    rtk_port_speed_t rtk_speed;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    rv =  rtk_port_speedDuplex_get(unit, port, &rtk_speed, &duplex);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d get fail, rv:%d\n", unit, port, rv);
        return rv;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d rtk_speed:%d rtk_duplex:%d get success\n", unit, port, rtk_speed, duplex);
    /* when link down, speed conf abnormal */
    rv =  rtk_port_phyLinkStatus_get(unit, port, &link_sta);
    if (!link_sta || rv) {
        *p_value = CTC_PORT_SPEED_1G;
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "unit:%d port:%d link:%d rv:%d, speed always 1G\n", unit, port, link_sta, rv);
        return RT_ERR_OK;
    }

    /* return ctc speed type */
    switch (rtk_speed) {
    case PORT_SPEED_1000M:
        *p_value = CTC_PORT_SPEED_1G;
        break;
    case PORT_SPEED_100M:
        *p_value = CTC_PORT_SPEED_100M;
        break;
    case PORT_SPEED_10M:
        *p_value = CTC_PORT_SPEED_10M;
        break;
    default:
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d invalid rtk_speed:%d\n", unit, port, rtk_speed);
        return RT_ERR_FAILED;
    }
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d speed:%d rtk_speed:%d get success\n", unit, port, *p_value, rtk_speed);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_set_port_auto_neg_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    if (!enable) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "unit:%d port:%d en:0 not support!\n", unit, port);
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d auto_neg_en:%d set not support\n", unit, port, enable);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_get_port_auto_neg_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    *p_enable = 1;

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d auto_neg_en:%d get not support\n", unit, port, *p_enable);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_set_port_loopback(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    rv =  rtk_port_phyLoopBackEnable_set(unit, port, enable);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d en:%d set fail, rv:%d\n", unit, port, enable, rv);
    } else {
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d en:%d set success\n", unit, port, enable);
    }

    return rv;
}

int32 cust_extphy_rtk_get_port_loopback(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    rv =  rtk_port_phyLoopBackEnable_get(unit, port, p_enable);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d get fail, rv:%d\n", unit, port, rv);
    } else {
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d en:%d get success\n", unit, port, *p_enable);
    }

    return rv;
}

int32 cust_extphy_rtk_linkup_event(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* user_data)
{
    int32 rv;
    uint32 unit, port, ctc_port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d change to up\n", unit, port);

    if (dev_autoneg_off_g) {
        ctc_port = parse_rtk_port(port);
        pthread_mutex_lock(&speed_update_pending_mutex[ctc_port]);
        speed_update_flag[ctc_port] = 1;
        pthread_mutex_unlock(&speed_update_pending_mutex[ctc_port]);
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "ctc_port:%d ready to update speed\n", ctc_port);
    }

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_linkdown_event(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* user_data)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d change to down\n", unit, port);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_set_port_unidir_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d unidir_en:%d set not support\n", unit, port, enable);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_get_port_unidir_en(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_enable)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    /* rtk not support */
    *p_enable = 0;

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_set_port_medium(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 value)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d medium:%d set not support\n", unit, port, value);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_get_port_medium(uint8 lchip, ctc_chip_mdio_para_t* param, uint32* p_value)
{
    int32 rv;
    uint32 unit, port;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    *p_value = 0;

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d medium:%d get not support\n", unit, port, *p_value);

    return RT_ERR_OK;
}

int32 cust_extphy_rtk_set_ext_attr(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value)
{
    return RT_ERR_OK;
/*
    int32 rv;
    uint32 unit, port;
    uint32 base_port, sdsid;
    rtk_sds_eyeParam_t eye_p;
    uint32 value, i;
    uint32 values[PHY_MAX_PARAMS];
    char *value_p;
    char *pch;

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    memset(&values, 0, sizeof(values));
    value_p = (char*)p_value;
    pch = strtok(value_p, PHY_PARAM_SPLIT);
    i = 0;
    while (pch) {
        c2int(pch, &values[i]);
        i++;
        pch = strtok(NULL, PHY_PARAM_SPLIT);
    }
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d type:%d set start...\n", unit, port, type);

    switch (type) {
    case CTC_PORT_PROP_PHY_EYEPARAM_AMP:
        memset(&eye_p, 0, sizeof(rtk_sds_eyeParam_t));
        rv = cust_rtk_get_port_serdes_id(unit, port, &sdsid);
        if (rv) {
            CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d get_port_serdes_id fail, rv:%d\n",
                unit, port, rv);
            return rv;
        }

        value = values[0];
        eye_p.pre_en = 1;
        eye_p.pre_amp = value & 0xff;
        eye_p.main_en = 1;
        eye_p.main_amp = (value & 0xff00) >> 8;
        eye_p.post_en = 1;
        eye_p.post_amp = (value & 0xff0000) >> 16;

        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "eye %d %d %d\n", eye_p.pre_amp, eye_p.main_amp, eye_p.post_amp);
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

        break;
    case CTC_PORT_PROP_PHY_REG_WRITE:
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "reg write page:0x%x reg:%d val:0x%x\n", values[0], values[1], values[2]);
        rv = cust_rtk_mdio_write(unit, port, values[0], values[1], values[2]);
        if (rv) {
            CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d cust_rtk_mdio_write fail, rv:%d\n", unit, port, sdsid, rv);
            return rv;
        }
        break;
    default:
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "type:%d not support!\n", type);
        return RT_ERR_FAILED;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d type:%d set success\n", unit, port, type);

    return rv;
    */
}

int32 cust_extphy_rtk_get_ext_attr(uint8 lchip, ctc_chip_mdio_para_t* param, uint32 type, void* p_value)
{
    return RT_ERR_OK;
    /*
    int32 rv;
    uint32 unit, port;
    uint32 base_port, sdsid;
    rtk_sds_eyeParam_t eye_p;
    rtk_port_speed_t speed;
    char *value_p;
    char *pch;
    uint32 value, i;
    uint32 values[PHY_MAX_PARAMS];
    char params[PHY_MAX_PARAMS_CHAR];

    value_p = (char*)p_value;
    memset(params, 0, sizeof(params));
    strcpy(params, value_p);

    memset(&values, 0, sizeof(values));
    pch = strtok(params, PHY_PARAM_SPLIT);
    i = 0;
    while (pch) {
        c2int(pch, &values[i]);
        i++;
        pch = strtok(NULL, PHY_PARAM_SPLIT);
    }

    value_p = (char*)p_value;
    memset(value_p, 0, strlen(params) + 1);

    rv = cust_get_ctc_port_info(lchip, param, &unit, &port);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_WARN, "rtk may not inited\n");
        return RT_ERR_OK;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d type:%d get start...\n", unit, port, type);

    switch (type) {
    case CTC_PORT_PROP_PHY_EYEPARAM_AMP:
        memset(&eye_p, 0, sizeof(rtk_sds_eyeParam_t));
        rv = cust_rtk_get_port_serdes_id(unit, port, &sdsid);
        if (rv) {
            CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d get_port_serdes_id fail, rv:%d\n",
                unit, port, rv);
            return rv;
        }

        rv = cust_rtk_get_base_port(unit, port, &base_port);
        if (rv) {
            CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d get_base_port fail, rv:%d\n",
                unit, port, rv);
            return rv;
        }

        rv = rtk_port_phySdsEyeParam_get(unit, base_port, sdsid, &eye_p);
        if (rv) {
            CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d base_port:%d sdsid:%d phySdsEyeParam_get fail, rv:%d\n",
                unit, base_port, sdsid, rv);
            return rv;
        }

        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "eye %d %d %d\n", eye_p.pre_amp, eye_p.main_amp, eye_p.post_amp);
        value = 0x0;
        value |= eye_p.pre_amp;
        value |= (eye_p.main_amp << 8);
        value |= (eye_p.post_amp << 16);

        sprintf(value_p, "0x%x", value);
        break;
    case CTC_PORT_PROP_PHY_SPEED:
        rv = cust_extphy_rtk_get_port_speed(lchip, param, &speed);
        if (rv) {
            CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d speed_get fail, rv:%d\n",
                unit, port, rv);
            return rv;
        }
        sprintf(value_p, "%d", speed);
        break;

    case CTC_PORT_PROP_PHY_REG_READ:
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "reg read page:0x%x reg:%d \n", values[0], values[1]);
        rv = cust_rtk_mdio_read(unit, port, values[0], values[1], &value);
        if (rv) {
            CUST_RTK_LOG(CUST_RT_LOG_ERR, "unit:%d port:%d cust_rtk_mdio_read fail, rv:%d\n", unit, port, rv);
            return rv;
        }
        sprintf(value_p, "0x%x", value);
        break;

    default:
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "type:%d not support!\n", type);
        return RT_ERR_FAILED;
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "unit:%d port:%d type:%d value:%s get success\n", unit, port, type, value_p);

    return rv;
    */
}

ctc_phy_driver_t ctc_chip_phy_rtk_api =
{
    .init = cust_extphy_rtk_init,
    .deinit = cust_extphy_rtk_deinit,
    .set_port_en = cust_extphy_rtk_set_port_en,
    .get_port_en = cust_extphy_rtk_get_port_en,
    .set_port_duplex_en = cust_extphy_rtk_set_port_duplex_en,
    .get_port_duplex_en = cust_extphy_rtk_get_port_duplex_en,
    .set_port_speed = cust_extphy_rtk_set_port_speed,
    .get_port_speed = cust_extphy_rtk_get_port_speed,
    .set_port_auto_neg_en = cust_extphy_rtk_set_port_auto_neg_en,
    .get_port_auto_neg_en = cust_extphy_rtk_get_port_auto_neg_en,
    .set_port_loopback = cust_extphy_rtk_set_port_loopback,
    .get_port_loopback = cust_extphy_rtk_get_port_loopback,
    .get_link_up_status = cust_extphy_rtk_get_link_up_status,
    .linkup_event = cust_extphy_rtk_linkup_event,
    .linkdown_event = cust_extphy_rtk_linkdown_event,
    .set_port_unidir_en = cust_extphy_rtk_set_port_unidir_en,
    .get_port_unidir_en = cust_extphy_rtk_get_port_unidir_en,
    .set_port_medium = cust_extphy_rtk_set_port_medium,
    .get_port_medium = cust_extphy_rtk_get_port_medium,
    .set_ext_attr = cust_extphy_rtk_set_ext_attr,
    .get_ext_attr = cust_extphy_rtk_get_ext_attr,
};

void *cust_speed_update_thread(void *arg)
{
    uint32 rtk_port, ctc_port;
    int i, rv;
    ctc_port_speed_t ctc_speed;
    rtk_port_duplex_t duplex;
    rtk_port_speed_t rtk_speed;

    while (1) {
        if (!rtk_inited_g) {
            sleep(1);
            continue;
        }

        if (!dev_autoneg_off_g) {
            break;
        }

        if (!ctc_port_autoneg_off) {
            for (i = 0; i < 48; i++) {
                ctc_port = parse_rtk_port(cust_port_descp_48e4x[i].mac_id);
                rv = cust_ctcs_port_set_property(0, ctc_port, CTC_PORT_PROP_AUTO_NEG_EN, 0);
                CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "ctc_port:%d set ctc_autoneg off end, rv:%d\n", ctc_port, rv);
            }
            ctc_port_autoneg_off = 1;
        }

        for (i = 0; i < 48; i++) {
            rtk_port = cust_port_descp_48e4x[i].mac_id;
            ctc_port = parse_rtk_port(rtk_port);

            if (speed_update_flag[ctc_port]) {
                rv = rtk_port_speedDuplex_get(0, rtk_port, &rtk_speed, &duplex);
                if (rv) {
                    CUST_RTK_LOG(CUST_RT_LOG_ERR, "rtk_port:%d get speed fail, rv:%d\n", rtk_port, rv);
                    continue;
                }

                switch (rtk_speed) {
                case PORT_SPEED_1000M:
                    ctc_speed = CTC_PORT_SPEED_1G;
                    break;
                case PORT_SPEED_100M:
                    ctc_speed = CTC_PORT_SPEED_100M;
                    break;
                case PORT_SPEED_10M:
                    ctc_speed = CTC_PORT_SPEED_10M;
                    break;
                default:
                    CUST_RTK_LOG(CUST_RT_LOG_ERR, "invalid rtk_speed:%d\n", rtk_speed);
                    continue;
                }

                pthread_mutex_lock(&speed_update_pending_mutex[ctc_port]);
                rv = cust_ctcs_port_set_speed(0, ctc_port, ctc_speed);
                CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "ctc_port:%d set speed:%d end, rv:%d\n", ctc_port, ctc_speed, rv);

                speed_update_flag[ctc_port] = 0;
                pthread_mutex_unlock(&speed_update_pending_mutex[ctc_port]);
            }
        }
        sleep(1);
    }
    return NULL;
}

void cust_phy_setting(void)
{
    int i, rv;
    pthread_t p_id;

    for (i = 0; i < MAX_PORT_NUM; i++) {
        rv = pthread_mutex_init(&speed_update_pending_mutex[i], NULL);
        if (rv) {
            CUST_RTK_LOG(CUST_RT_LOG_ERR, " %d pthread_mutex_init fail, rv:%d\n", i, rv);
        }
    }
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "mutex init end\n");

    rv = pthread_create(&p_id, NULL, cust_speed_update_thread, NULL);
    if (rv) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "pthread_create cust_speed_update_thread fail, rv:%d\n", rv);
    } else {
        pthread_detach(p_id);
        sleep(1);
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "pthread_create cust_speed_update_thread success\n");
    }
}

void ctc_app_phy_driver_init(uint8 lchip)
{
    ctc_chip_phy_shim_t phy_shim;
    ctc_phy_driver_t* phy_drv;
    int32 ret;
    void* ctcsdk_dl_hdl;
    ctcs_chip_set_property_f ctc_set_chip_prop;

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "init start\n");

    ctcsdk_dl_hdl = dlopen(CTCSDK_LIB_DL_PATH, RTLD_LAZY);
    if (!ctcsdk_dl_hdl) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "%s\n", dlerror());
        dlclose(ctcsdk_dl_hdl);
        return;
    }

    ctc_set_chip_prop = (ctcs_chip_set_property_f)dlsym(ctcsdk_dl_hdl, CTCSDK_CHIP_PROP_SET_SYMBOL);
    if (!ctc_set_chip_prop) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "%s\n", dlerror());
        dlclose(ctcsdk_dl_hdl);
        return;
    }

    cust_ctcs_port_set_property = (ctcs_port_set_property_f)dlsym(ctcsdk_dl_hdl, CTCSDK_PORT_PROP_SET_SYMBOL);
    if (!cust_ctcs_port_set_property) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "%s\n", dlerror());
    } else {
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "dlsym %s success\n", CTCSDK_PORT_PROP_SET_SYMBOL);
    }

    cust_ctcs_port_set_speed = (ctcs_port_set_speed_f)dlsym(ctcsdk_dl_hdl, CTCSDK_PORT_SPEED_SET_SYMBOL);
    if (!cust_ctcs_port_set_speed) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "%s\n", dlerror());
    } else {
        CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "dlsym %s success\n", CTCSDK_PORT_SPEED_SET_SYMBOL);
    }

    dlclose(ctcsdk_dl_hdl);
    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "dlsym %s success\n", CTCSDK_CHIP_PROP_SET_SYMBOL);

    cust_phy_setting();
    CUST_RTK_LOG(CUST_RT_LOG_ERR, "cust_phy_setting end\n");

    phy_drv = &ctc_chip_phy_rtk_api;
    memset(&phy_shim, 0, sizeof(ctc_chip_phy_shim_t));
    phy_shim.phy_id_mask = PHY_ID_MASK;
    phy_shim.event_mode = CTC_CHIP_PHY_SHIM_EVENT_MODE_POLLING;
    phy_shim.poll_interval = 100; /* ms */

    memset(phy_shim.phy_name, 0, CTC_CHIP_PHY_NAME_MAX_LEN);
    memcpy(phy_shim.phy_name, PHY_NAME_RTL8218D, CTC_CHIP_PHY_NAME_MAX_LEN);
    phy_shim.phy_id = PHY_TYPE_RTL8218D;
    memcpy(&phy_shim.driver, phy_drv, sizeof(ctc_phy_driver_t));
    ret = ctc_set_chip_prop(0, CTC_CHIP_PROP_REGISTER_PHY, (void*)&phy_shim);
    if (ret) {
         CUST_RTK_LOG(CUST_RT_LOG_ERR, "chip REGISTER_PHY %s fail, rv:%d\n", phy_shim.phy_name, ret);
    } else {
         CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "chip REGISTER_PHY %s success\n", phy_shim.phy_name);
    }

    memset(phy_shim.phy_name, 0, CTC_CHIP_PHY_NAME_MAX_LEN);
    memcpy(phy_shim.phy_name, PHY_NAME_RTL8218E, CTC_CHIP_PHY_NAME_MAX_LEN);
    phy_shim.phy_id = PHY_TYPE_RTL8218E;
    memcpy(&phy_shim.driver, phy_drv, sizeof(ctc_phy_driver_t));
    ret = ctc_set_chip_prop(0, CTC_CHIP_PROP_REGISTER_PHY, (void*)&phy_shim);
    if (ret) {
         CUST_RTK_LOG(CUST_RT_LOG_ERR, "chip REGISTER_PHY %s fail, rv:%d\n", phy_shim.phy_name, ret);
    } else {
         CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "chip REGISTER_PHY %s success\n", phy_shim.phy_name);
    }

    memset(phy_shim.phy_name, 0, CTC_CHIP_PHY_NAME_MAX_LEN);
    memcpy(phy_shim.phy_name, PHY_NAME_RTL8214FC, CTC_CHIP_PHY_NAME_MAX_LEN);
    phy_shim.phy_id = PHY_TYPE_RTL8214FC;
    memcpy(&phy_shim.driver, phy_drv, sizeof(ctc_phy_driver_t));
    ret = ctc_set_chip_prop(0, CTC_CHIP_PROP_REGISTER_PHY, (void*)&phy_shim);
    if (ret) {
        CUST_RTK_LOG(CUST_RT_LOG_ERR, "chip REGISTER_PHY %s fail, rv:%d\n", phy_shim.phy_name, ret);
    } else {
         CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "chip REGISTER_PHY %s success\n", phy_shim.phy_name);
    }

    CUST_RTK_LOG(CUST_RT_LOG_NORMAL, "init end\n");
}
