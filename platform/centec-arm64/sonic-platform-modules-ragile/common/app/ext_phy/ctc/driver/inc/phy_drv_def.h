/**
 @file phy_drv_def.h
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/
#ifndef _PHY_DRV_DRV_H
#define _PHY_DRV_DRV_H
#include "sal_types.h"

#define CTC_PHY_VERSION  "v1.0.2"

#ifndef RESULT_OK
#define RESULT_OK 0
#endif

#ifndef RESULT_ERROR
#define RESULT_ERROR -1
#endif

#define CTC_MAX_PHY_PORT_NUM 255 /* the same as SYS_USW_MAX_PHY_PORT */

typedef int32 (*ctc_phy_sem_take_t)(uint32 , uint32 );
typedef int32 (*ctc_phy_sem_give_t)(uint32 );

/** @enum phy_chip_index_e */
enum phy_chip_index_e
{
    PHY_CHIP_INVALID,
    PHY_CHIP_1,
    PHY_CHIP_2,
    PHY_CHIP_3,
    PHY_CHIP_4,
    PHY_CHIP_5,
    PHY_CHIP_6,
    PHY_CHIP_7,
    PHY_CHIP_8,
    PHY_CHIP_9,
    PHY_CHIP_10,
    PHY_CHIP_11,
    PHY_CHIP_12,
    PHY_CHIP_MAX
};

/* PHY IDs */
#ifdef PHY_ID_REVERSE
#define PHY_TYPE_VSC8512_A      0x06e20007
#define PHY_TYPE_VSC8512_B      0x06f30007
#define PHY_TYPE_MV88E1680      0x0ed40141
#define PHY_TYPE_MARS8P         0x408101e0
#define PHY_TYPE_MARS4C         0x404101e0
#define PHY_TYPE_RTL8128B       0xc981001c
#define PHY_TYPE_MARS1S_V1      0x20130078
#define PHY_TYPE_MARS1S         0x401301E0
#define PHY_TYPE_MARS1P_V1      0x20110078
#define PHY_TYPE_MARS1P         0x401101E0
#define PHY_TYPE_UNKNOWN        0xffffffff
#else
#define PHY_TYPE_VSC8512_A      0x000706e2
#define PHY_TYPE_VSC8512_B      0x000706f3
#define PHY_TYPE_MV88E1680      0x01410ed4
#define PHY_TYPE_MARS8P         0x01e04081
#define PHY_TYPE_MARS4C         0x01e04041
#define PHY_TYPE_RTL8128B       0x001cc981
#define PHY_TYPE_MARS1S_V1      0x00782013
#define PHY_TYPE_MARS1S         0x01E04013
#define PHY_TYPE_MARS1P_V1      0x00782011
#define PHY_TYPE_MARS1P         0x01E04011
#define PHY_TYPE_UNKNOWN        0xffffffff
#endif
/* PHY STATUS */
#define GLB_DISABLE   0
#define GLB_ENABLE     1

#define GLB_LINK_DOWN   0
#define GLB_LINK_UP     1

#define GLB_DUPLEX_HALF   0
#define GLB_DUPLEX_FULL   1
#define GLB_DUPLEX_MAX    2

#define GLB_PORT_TYPE_COPPER 0/*twisted pair */
#define GLB_PORT_TYPE_FIBER 1   /* optical*/

/*PHY REG*/
#define PHY_CTL_REG             0x0          /*bit 12:auto; 6,13: 10M-0,100M-1,1000M-2; 8:Full-1,Half-0*/
#define PHY_STATUS_REG          0x1
#define PHY_IDENTIFIER1_REG     0x2
#define PHY_IDENTIFIER2_REG     0x3
#define PHY_AN_ADVERTI_REG      0x4         /*bit 8,7,6,5: 100F,100H,10F,10H*/
#define PHY_AN_LP_ADVERTI_REG   0x5
#define PHY_1G_BASET_CTL_REG    0x9         /*bit 9,8 : 1000F, 1000H*/
#define PHY_INT_STATUS_REG      0x1a

/* Register 0: Control Register */
#define Reset_OFFSET                     (15)
#define Reset_MASK                       (0x1U<<Reset_OFFSET)
#define Loopback_OFFSET                  (14)
#define Loopback_MASK                    (0x1U<<Loopback_OFFSET)
#define SpeedSelection0_OFFSET           (13)
#define SpeedSelection0_MASK             (0x1U<<SpeedSelection0_OFFSET)
#define AutoNegotiationEnable_OFFSET     (12)
#define AutoNegotiationEnable_MASK       (0x1U<<AutoNegotiationEnable_OFFSET)
#define PowerDown_OFFSET                 (11)
#define PowerDown_MASK                   (0x1U<<PowerDown_OFFSET)
#define Isolate_OFFSET                   (10)
#define Isolate_MASK                     (0x1U<<Isolate_OFFSET)
#define RestartAutoNegotiation_OFFSET    (9)
#define RestartAutoNegotiation_MASK      (0x1U<<RestartAutoNegotiation_OFFSET)
#define DuplexMode_OFFSET                (8)
#define DuplexMode_MASK                  (0x1U<<DuplexMode_OFFSET)
#define CollisionTest_OFFSET             (7)
#define CollisionTest_MASK               (0x1U<<CollisionTest_OFFSET)
#define SpeedSelection1_OFFSET           (6)
#define SpeedSelection1_MASK             (0x1U<<SpeedSelection1_OFFSET)

/* Register 1: Status Register */
#define _100Base_T4_OFFSET               (15)
#define _100Base_T4_MASK                 (0x1U<<_100Base_T4_OFFSET)
#define _100Base_TX_FD_OFFSET            (14)
#define _100Base_TX_FD_MASK              (0x1U<<_100Base_TX_FD_OFFSET )
#define _100Base_TX_HD_OFFSET            (13)
#define _100Base_TX_HD_MASK              (0x1U<<_100Base_TX_HD_OFFSET)
#define _10Base_T_FD_OFFSET              (12)
#define _10Base_T_FD_MASK                (0x1U<<_10Base_T_FD_OFFSET)
#define _10Base_T_HD_OFFSET              (11)
#define _10Base_T_HD_MASK                (0x1U<<_10Base_T_HD_OFFSET)
#define _100Base_T2_FD_OFFSET            (10)
#define _100Base_T2_FD_MASK              (0x1U<<_100Base_T2_FD_OFFSET)
#define _100Base_T2_HD_OFFSET            (9)
#define _100Base_T2_HD_MASK              (0x1U<<_100Base_T2_HD_OFFSET)
#define ExtendStatus_OFFSET              (8)
#define ExtendStatus_MASK                (0x1U<<ExtendStatus_OFFSET)
#define MFPreambleSuppression_OFFSET     (6)
#define MFPreambleSuppression_MASK       (0x1U<<MFPreambleSuppression_OFFSET)
#define AutoNegotiationComplete_OFFSET   (5)
#define AutoNegotiationComplete_MASK     (0x1U<<AutoNegotiationComplete_OFFSET )
#define RemoteFault_OFFSET               (4)
#define RemoteFault_MASK                 (0x1U<<RemoteFault_OFFSET)
#define AutoNegotiationAbility_OFFSET    (3)
#define AutoNegotiationAbility_MASK      (0x1U<<AutoNegotiationAbility_OFFSET )
#define LinkStatus_OFFSET                (2)
#define LinkStatus_MASK                  (0x1U<<LinkStatus_OFFSET)
#define JabberDetect_OFFSET              (1)
#define JabberDetect_MASK                (0x1U<<JabberDetect_OFFSET)
#define ExtendedCapability_OFFSET        (0)
#define ExtendedCapability_MASK          (0x1U<<ExtendedCapability_OFFSET)

/* Register 2: PHY Identifier 1 */
#define OUI_03_18_OFFSET                 (0)
#define OUI_03_18_MASK                   (0xFFFFU<<OUI_03_18_OFFSET)

/* Register 3: PHY Identifier 2 */
#define OUI_19_24_OFFSET                 (10)
#define OUI_19_24_MASK                   (0x3FU<<OUI_19_24_OFFSET)
#define ModelNumber_OFFSET               (4)
#define ModelNumber_MASK                 (0x3FU<<ModelNumber_OFFSET)
#define RevisionNumber_OFFSET            (0)
#define RevisionNumber_MASK              (0xFU<<RevisionNumber_OFFSET)

/* Register 4: Auto-Negotiation Advertisement */
#define NextPage_R4_OFFSET               (15)
#define NextPage_R4_MASK                 (0x1U<<NextPage_R4_OFFSET)
#define Acknowledge_R4_OFFSET            (14)
#define Acknowledge_R4_MASK              (0x1U<<Acknowledge_R4_OFFSET)
#define RemoteFault_R4_OFFSET            (13)
#define RemoteFault_R4_MASK              (0x1U<<RemoteFault_R4_OFFSET)
#define AsymmetricPause_R4_OFFSET        (11)
#define AsymmetricPause_R4_MASK          (0x1U<<AsymmetricPause_R4_OFFSET)
#define Pause_R4_OFFSET                  (10)
#define Pause_R4_MASK                    (0x1U<<Pause_R4_OFFSET)
#define _100Base_T4_R4_OFFSET            (9)
#define _100Base_T4_R4_MASK              (0x1U<<_100Base_T4_R4_OFFSET)
#define _100Base_TX_FD_R4_OFFSET         (8)
#define _100Base_TX_FD_R4_MASK           (0x1U<<_100Base_TX_FD_R4_OFFSET)
#define _100Base_TX_R4_OFFSET            (7)
#define _100Base_TX_R4_MASK              (0x1U<<_100Base_TX_R4_OFFSET)
#define _10Base_T_FD_R4_OFFSET           (6)
#define _10Base_T_FD_R4_MASK             (0x1U<<_10Base_T_FD_R4_OFFSET)
#define _10Base_T_R4_OFFSET              (5)
#define _10Base_T_R4_MASK                (0x1U<<_10Base_T_R4_OFFSET)
#define SelectorField_R4_OFFSET          (0)
#define SelectorField_R4_MASK            (0x1FU<<SelectorField_R4_OFFSET)

/* Register 4: 1000Base-X Auto-Negotiation Advertisement */
#define _1000BaseX_NextPage_R4_OFFSET          (15)
#define _1000BaseX_NextPage_R4_MASK            (0x1U<<_1000BaseX_NextPage_R4_OFFSET)
#define _1000BaseX_RemoteFault_R4_OFFSET       (12)
#define _1000BaseX_RemoteFault_R4_MASK         (0x3U<<_1000BaseX_RemoteFault_R4_OFFSET)
#define _1000BaseX_AsymmetricPause_R4_OFFSET   (8)
#define _1000BaseX_AsymmetricPause_R4_MASK     (0x1U<<_1000BaseX_AsymmetricPause_R4_OFFSET)
#define _1000BaseX_Pause_R4_OFFSET             (7)
#define _1000BaseX_Pause_R4_MASK               (0x1U<<_1000BaseX_Pause_R4_OFFSET)
#define _1000BaseX_HalfDuplex_R4_OFFSET        (6)
#define _1000BaseX_HalfDuplex_R4_MASK          (0x1U<<_1000BaseX_HalfDuplex_R4_OFFSET)
#define _1000BaseX_FullDuplex_R4_OFFSET        (5)
#define _1000BaseX_FullDuplex_R4_MASK          (0x1U<<_1000BaseX_FullDuplex_R4_OFFSET)

/* Register 5: Auto-Negotiation Link Partner Ability */
#define NextPage_R5_OFFSET               (15)
#define NextPage_R5_MASK                 (0x1U<<NextPage_R5_OFFSET)
#define Acknowledge_R5_OFFSET            (14)
#define Acknowledge_R5_MASK              (0x1U<<Acknowledge_R5_OFFSET)
#define RemoteFault_R5_OFFSET            (13)
#define RemoteFault_R5_MASK              (0x1U<<RemoteFault_R5_OFFSET)
#define AsymmetricPause_R5_OFFSET        (11)
#define AsymmetricPause_R5_MASK          (0x1U<<AsymmetricPause_R5_OFFSET)
#define Pause_R5_OFFSET                  (10)
#define Pause_R5_MASK                    (0x1U<<Pause_R5_OFFSET)
#define _100Base_T4_R5_OFFSET            (9)
#define _100Base_T4_R5_MASK              (0x1U<<_100Base_T4_R5_OFFSET)
#define _100Base_TX_FD_R5_OFFSET         (8)
#define _100Base_TX_FD_R5_MASK           (0x1U<<_100Base_TX_FD_R5_OFFSET)
#define _100Base_TX_R5_OFFSET            (7)
#define _100Base_TX_R5_MASK              (0x1U<<_100Base_TX_R5_OFFSET)
#define _10Base_T_FD_R5_OFFSET           (6)
#define _10Base_T_FD_R5_MASK             (0x1U<<_10Base_T_FD_R5_OFFSET)
#define _10Base_T_R5_OFFSET              (5)
#define _10Base_T_R5_MASK                (0x1U<<_10Base_T_R5_OFFSET)
#define SelectorField_R5_OFFSET          (0)
#define SelectorField_R5_MASK            (0x1FU<<SelectorField_R5_OFFSET)

/* Register 5: 1000Base-X Auto-Negotiation Link Parnter Ability */
#define _1000BaseX_NextPage_R5_OFFSET          (15)
#define _1000BaseX_NextPage_R5_MASK            (0x1U<<_1000BaseX_NextPage_R5_OFFSET)
#define _1000BaseX_Acknowledge_R5_OFFSET       (14)
#define _1000BaseX_Acknowledge_R5_MASK         (0x1U<<_1000BaseX_Acknowledge_R5_OFFSET)
#define _1000BaseX_RemoteFault_R5_OFFSET       (12)
#define _1000BaseX_RemoteFault_R5_MASK         (0x3U<<_1000BaseX_RemoteFault_R5_OFFSET)
#define _1000BaseX_AsymmetricPause_R5_OFFSET   (8)
#define _1000BaseX_AsymmetricPause_R5_MASK     (0x1U<<_1000BaseX_AsymmetricPause_R5_OFFSET)
#define _1000BaseX_Pause_R5_OFFSET             (7)
#define _1000BaseX_Pause_R5_MASK               (0x1U<<_1000BaseX_Pause_R5_OFFSET)
#define _1000BaseX_HalfDuplex_R5_OFFSET        (6)
#define _1000BaseX_HalfDuplex_R5_MASK          (0x1U<<_1000BaseX_HalfDuplex_R5_OFFSET)
#define _1000BaseX_FullDuplex_R5_OFFSET        (5)
#define _1000BaseX_FullDuplex_R5_MASK          (0x1U<<_1000BaseX_FullDuplex_R5_OFFSET)
#define _1000BaseX_SelectorField_R5_OFFSET     (0)
#define _1000BaseX_SelectorField_R5_MASK       (0x1FU<<_1000BaseX_SelectorField_R5_OFFSET)

/* Register 9: 1000Base-T Control Register */
#define TestMode_OFFSET                                 (13)
#define TestMode_MASK                                   (0x7U<<TestMode_OFFSET)
#define MasterSlaveManualConfigurationEnable_OFFSET     (12)
#define MasterSlaveManualConfigurationEnable_MASK       (0x1U<<MasterSlaveManualConfigurationEnable_OFFSET)
#define MasterSlaveConfigurationValue_OFFSET            (11)
#define MasterSlaveConfigurationValue_MASK              (0x1U<<MasterSlaveConfigurationValue_OFFSET)
#define PortType_OFFSET                                 (10)
#define PortType_MASK                                   (0x1U<<PortType_OFFSET)
#define _1000Base_TFullDuplex_OFFSET                    (9)
#define _1000Base_TFullDuplex_MASK                      (0x1U<<_1000Base_TFullDuplex_OFFSET)
#define _1000Base_THalfDuplex_OFFSET                    (8)
#define _1000Base_THalfDuplex_MASK                      (0x1U<<_1000Base_THalfDuplex_OFFSET)

/** @enum glb_port_speed_e */
enum glb_port_speed_e
{
    GLB_SPEED_AUTO,
    GLB_SPEED_10M,
    GLB_SPEED_100M,
    GLB_SPEED_1G,
    GLB_SPEED_10G,
    GLB_SPEED_40G,
    GLB_SPEED_100G,
    GLB_SPEED_5G,
    GLB_SPEED_2_5G,
    GLB_SPEED_25G,
    GLB_SPEED_50G,
    GLB_SPEED_MAX
};
typedef enum glb_port_speed_e glb_port_speed_t;

/** @enum glb_lb_phy_e */
enum glb_lb_phy_e
{
    GLB_LB_NONE,/**< no loopback */
    GLB_LB_PHY_FAR,/**< external loopback */
    GLB_LB_PHY_NEAR, /**< internal loopback */
    GLB_LB_MAX
};
typedef enum glb_lb_phy_e glb_lb_phy_t;

/** @enum glb_phy_mac_interface_e */
enum glb_phy_mac_interface_e
{
    GLB_MAC_INTERFACE_NONE = -1,
    GLB_MAC_INTERFACE_SGMII = 0, /**< SGMII for phy mac interface */
    GLB_MAC_INTERFACE_SERDES, /**< Serdes mode for port without phy */
    GLB_MAC_INTERFACE_QSGMII, /**< QSGMII for phy mac interface */
    GLB_MAC_INTERFACE_RGMII, /**< RGMII for phy mac interface */
    GLB_MAC_INTERFACE_MAX,
};
typedef enum glb_phy_mac_interface_e glb_mac_interface_t;

/** @enum glb_media_interface_e */
enum glb_media_interface_e
{
    GLB_MEDIA_RJ45, /**< Cat5*/
    GLB_MEDIA_1000BX, /**< 1000BASE-X*/
    GLB_MEDIA_XFP,/**< XFP for fiber*/
    GLB_MEDIA_SFP_PLUS,/**< SFP+ for fiber*/
    GLB_MEDIA_PASS_THROUGH, /**< SerDes(Passthrough) */
    GLB_MEDIA_FI_100FX, /**<100FX*/
    GLB_MEDIA_AMS_START=0x40,
    GLB_MEDIA_AMS_CU_PASSTHRU, /**<Cat5 or SerDes(Passthrough), cat5 prefer.*/
    GLB_MEDIA_AMS_FI_PASSTHRU, /**<Cat5 or SerDes(Passthrough), SerDes prefer.*/
    GLB_MEDIA_AMS_CU_1000BX, /**<Cat5 or 1000BASE-X, cat5 prefer.*/
    GLB_MEDIA_AMS_FI_1000BX, /**<Cat5 or 1000BASE-X, 1000BASE-X prefer.*/
    GLB_MEDIA_AMS_CU_100FX, /**<Cat5 or 100FX, cat5 prefer.*/
    GLB_MEDIA_AMS_FI_100FX,/**<Cat5 or 100FX, 100FX prefer.*/
    GLB_MEDIA_QSFP_PLUS,/**< QSFP+ for fiber*/
};
typedef enum glb_media_interface_e glb_media_interface_t;

/**
 @struct phy_info_t
 */
typedef struct
{
    uint32 port_id;/**< port index */
    uint8 bus;/**< mdio bus index */
    uint8 phy_addr; /**< port mdio bus addr */
    uint8 ctl_id; /**< mdio slice id <0-1>*/
    uint32 phy_id;/**< phy identity */
    uint8 phy_chip_id;/**< phy chip id, defined as phy_chip_index_e */
    uint32 phy_base_port;/**< base port index on phy chip */
    uint32 phy_last_port;/**< last port index on phy chip */
    uint16 dev_no;/**< only usefull for xgphy */
    uint8 lchip;/**< local chip index */
    uint8 flag; /**< for post init or pre init */
    uint8 init_done; /**< for mask port init down */

    uint8 enable;/**< port enable */
    uint8 enable_status;/**< port enable status */
    uint8 duplex;/**< port duplex */
    uint8 duplex_status;/**< port duplex status */
    uint8 speed; /**< port speed, defined as ctc_port_speed_t */
    uint8 speed_status;/**< port speed status */
    uint8 auto_neg_en;/**< port auto-nego*/
    uint8 auto_neg_status;/**< port auto-nego status */
    uint8 mdium;/**< port mdium */
    uint8 mdium_status;/**< port mdium status */
    uint8 mac_if;/**< phy mac interface type, defined as glb_phy_mac_interface_e */
    uint8 loopback_mode;/**< phy loopback mode, defined as glb_lb_phy_e */
    uint8 loopback_status;/**< port loopback status */
    uint8 undir_en;/**< port undir */
    uint8 undir_status;/**< port undir status */
    uint8 link_up;/**< port link status */
    uint8 lds_result;/**< whether enable lds */
    uint8 port_type;/**< the port type being set */
    ctc_phy_sem_take_t sem_take;
    ctc_phy_sem_give_t sem_give;
} phy_info_t;

enum vct_status_e
{
    GLB_VCT_STATUS_CLOSED = 0,     /* VCT Mod is not start */
    GLB_VCT_STATUS_RUNNING,        /* VCT Mod is running   */
    GLB_VCT_STATUS_FINISHED,       /* VCT Mod is finished  */
    GLB_VCT_STATUS_MAX,
};
typedef enum vct_status_e vct_status_t;

enum pair_state_e
{
    GLB_PAIR_STATE_NORMAL = 0x0,                /* Correctly terminated pair */
    GLB_PAIR_STATE_ABNORMAL_TERMINATION = 0x1,  /* Abnormal termination */
    GLB_PAIR_STATE_ABNORMAL_SHORTED = 0x2,      /* Short pair */
    GLB_PAIR_STATE_ABNORMAL_OPEN = 0x3,         /* Open pair */
};
typedef enum pair_state_e pair_state_t;

struct pair_info_s
{
    uint16 pair_length;
    pair_state_t pair_status;
};
typedef struct pair_info_s pair_info_t;

struct port_cable_info_s
{
    pair_info_t pair_A;
    pair_info_t pair_B;
    pair_info_t pair_C;
    pair_info_t pair_D;
};
typedef struct port_cable_info_s port_cable_info_t;

struct lds_detail_s
{
    uint32 linkup;
    uint32 length;
    uint32 result;
};
typedef struct lds_detail_s lds_detail_t;

struct led_serial_s
{
    uint16 port_num;
    uint16 led_num;
};
typedef struct led_serial_s led_serial_t;

struct led_details_s
{
    uint16 act_low;
    uint16 bit_mask;
    uint16 port_en_ctrl;
    uint16 clk_en;
    uint16 data_en;
    uint16 burst_cycle;
    uint16 clk_cycle;
};
typedef struct led_details_s led_details_t;

struct led_blink_act_s
{
    uint16 led_blk_duty_cycle;
    uint16 led_blk_freq;
};
typedef struct led_blink_act_s led_blink_act_t;

struct led_force_s
{
    uint16 led_force_en;
    uint16 led_force_mode;
};
typedef struct led_force_s led_force_t;

struct link_status_s
{
    uint32 speed_status;/**< port speed status */
    uint32 duplex_status;/**< port duplex status */
    uint32 auto_neg_status;/**< port auto-nego status */
    uint32 link_up;/**< port link status */
    uint32 qsg_link_up;/**< qsgmii link status */
    uint32 qsg_speed_status;/**< qsgmii speed status */
    uint32 sg_link_up;              /**< sgmii/fiber link status */
    uint32 sg_speed_status;    /**< sgmii/fiber speed status */
};
typedef struct link_status_s link_status_t;

struct packet_generator_s
{
    uint16 packet_num;
    uint16 packet_len;
    uint16 addr_en;
    uint16 addr_da;
    uint16 addr_sa;
};
typedef struct packet_generator_s packet_generator_t;

struct packet_generator_count_s
{
    uint32 stream;
    uint32 rx_good;
    uint16 rx_error;
    uint32 tx_good;
    uint16 tx_error;
};
typedef struct packet_generator_count_s packet_generator_count_t;

struct packet_checker_s
{
    uint32 enable;
    uint32 stream;
};
typedef struct packet_checker_s packet_checker_t;

struct fast_link_down_s
{
    uint32 enable;
    uint32 delay;
};
typedef struct fast_link_down_s fast_link_down_t;

struct synce_s
{
    uint16 channel;
    uint16 enable;
    uint16 freq;
};
typedef struct synce_s synce_t;

struct prbs_en_s
{
    uint32 enable;
    uint32 prbs;
};
typedef struct prbs_en_s prbs_en_t;

struct test_mode_s
{
    uint32 mode;
    uint32 speed;
};
typedef struct test_mode_s test_mode_t;

struct prbs_result_s
{
    uint32 prbs;
    uint32 sync;
    uint32 error;
};
typedef struct prbs_result_s prbs_result_t;

struct phy_ext_s
{
    uint16 reg;
    uint16 value;
};
typedef struct phy_ext_s phy_ext_t;

struct phy_page_ext_s
{
    uint16 page;
    uint16 reg;
    uint16 value;
};
typedef struct phy_page_ext_s phy_page_ext_t;

/**
 @struct phy_manufacturers_t
 */
typedef struct {
	uint32 id;/**< PHY Identifier */
    uint32 id_mask;/**< PHY Identifier mask */
	char *name;/**< PHY name */
    /** callback for get driver for specific phy */
    int32 (* driver_get)(void **);
}phy_manufacturers_t;

/** @enum custom_prop_type_e
@ingroup PROTBL
*/
enum custom_prop_type_e
{
    PHY_CUSTOM_PREINIT = 1,
    PHY_CUSTOM_POSTINIT,
    PHY_SET_PKT_CK,
    PHY_GET_PKT_CK,
    PHY_GET_PKT_COUNT,
    PHY_SET_PKT_GEN,
    PHY_GET_PKT_GEN,
    PHY_SET_PKT_GEN_EN,
    PHY_GET_PKT_GEN_EN,
    PHY_SET_VCT_EN,
    PHY_GET_VCT_RESULT,
    PHY_SET_LDS_EN,
    PHY_GET_LDS_EN,
    PHY_GET_LDS_RESULT,
    PHY_GET_LINK_STATUS_DETAILS,
    PHY_SET_MDIMDIX_MODE,
    PHY_GET_MDIMDIX_MODE,
    PHY_SET_DOWNGRADE_EN,
    PHY_GET_DOWNGRADE_EN,
    PHY_SET_FASTLINKDOWN,
    PHY_GET_FASTLINKDOWN,
    PHY_SET_LED_EN,
    PHY_GET_LED_EN,
    PHY_SET_LED_MODE,
    PHY_GET_LED_MODE,
    PHY_SET_LED_GLB_CONFIG,
    PHY_GET_LED_GLB_CONFIG,
    PHY_SET_LED_SERIAL,
    PHY_GET_LED_SERIAL,
    PHY_SET_LED_BLINK,
    PHY_GET_LED_BLINK,
    PHY_SET_LED_BLINK_ACT,
    PHY_GET_LED_BLINK_ACT,
    PHY_SET_JUMBO,
    PHY_GET_JUMBO,
    PHY_SET_SYNCE,
    PHY_GET_SYNCE,
    PHY_SET_PRBS,
    PHY_GET_PRBS,
    PHY_SET_PRBS_CK,
    PHY_GET_PRBS_CK,
    PHY_GET_PRBS_RESULT,
    PHY_SET_TESTMODE,
    PHY_EXT_READ,
    PHY_EXT_WRITE,
    PHY_PAGE_READ,
    PHY_PAGE_WRITE,
    PHY_PAGE_EXT_READ,
    PHY_PAGE_EXT_WRITE,
    PHY_SET_SLEEP_EN,
    PHY_GET_SLEEP_EN,
    PHY_SET_EEE_EN,
    PHY_GET_EEE_EN,
    PHY_GET_EEE_STATUS,
    PHY_SET_FIB_TO_SGMII_EN,
    PHY_GET_FIB_TO_SGMII_EN,
    PHY_SET_CHIP_MODE,
    PHY_GET_CHIP_MODE,
    PHY_CUSTOM_MAX = 99,
};

#endif /*_PHY_DRV_DRV_H*/
