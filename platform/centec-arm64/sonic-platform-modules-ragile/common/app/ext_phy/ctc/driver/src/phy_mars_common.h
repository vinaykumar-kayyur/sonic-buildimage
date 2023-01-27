/**
 @file phy_drv_mars.h
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2020-11-17
 @version v1.0
*/
#include "sal.h"
#include "phy_drv_common.h"
#include "phy_drv_api.h"

#define PHY_MARS_SEM_TAKE \
    if (g_phy_port_info[port_id].sem_take) g_phy_port_info[port_id].sem_take(port_id, MARS_WAIT_FOREVER)
#define PHY_MARS_SEM_GIVE \
    if (g_phy_port_info[port_id].sem_give) g_phy_port_info[port_id].sem_give(port_id)

#define PHY_MARS_ERROR_RETURN(op) \
    { \
        int32 rv = (op); \
        if (rv < 0) \
        { \
            PHY_LOG_ERR("Fun:%s()  Line:%d ret:%d\n",__FUNCTION__,__LINE__, rv); \
            return (rv); \
        } \
    }

#define PHY_MARS_ERROR_RETURN_WITH_SEM_GIVE(op) \
    { \
        int32 rv = (op); \
        if (rv < 0) \
        { \
            PHY_LOG_ERR("Fun:%s()  Line:%d ret:%d\n",__FUNCTION__,__LINE__, rv); \
            PHY_MARS_SEM_GIVE;\
            return (rv); \
        } \
    }

#define MARS_OUT_SYNC   0
#define MARS_SYNC     1
#define MARS_OUT_EEE   0
#define MARS_EEE     1
#define MARS_WAIT_FOREVER             0
#define MARS_PAGE_REG             0xa000
#define MARS_PAGE_MASK             0x3
#define MARS_EXT_REG_ADDR     0x1e
#define MARS_EXT_REG_DATA     0x1f

#define MARS_SERIAL_LED_NUM_MAX     24

typedef enum mars_page_e
{
    MARS_PAGE_UTP,
    MARS_PAGE_QSGMII,
    MARS_PAGE_SGMII,
    MARS_PAGE_LDS,
    MARS_PAGE_FIBER_LED,  //4c
    MARS_PAGE_MAX,
}mars_page_t;

enum mars_port_type_e
{
    MARS_PORT_TYPE_COPPER,
    MARS_PORT_TYPE_FIBER,
    MARS_PORT_TYPE_MAX
};
typedef enum mars_port_type_e mars_port_type_t;

typedef enum mars_test_mode_e
{
    MARS_TEST_MODE_DISABLE,  /*normal operation mode*/
    MARS_TEST_MODE_1, /*Transmit waveform test*/
    MARS_TEST_MODE_2, /*Transmit jitter test as master*/
    MARS_TEST_MODE_3, /*Transmit jitter test as slave*/
    MARS_TEST_MODE_4, /*Transmit Distortion Test*/
    MARS_TEST_MODE_PRBS7, /*PRBS7 test*/
    MARS_TEST_MODE_PRBS10, /*PRBS10 test*/
    MARS_TEST_MODE_PRBS31, /*PRBS31 test*/
    MARS_TEST_MODE_MAX,
}mars_test_mode_t;

enum mars_led_mode_e /*Control each port's LED indicator symbol number and the information it indicates.*/
{                                        /*************************************************************************/
    MARS_LED_MODE0,       /**   each port has one LED indicator symbols,{1st led},to indicates:                           **
                                           **     MDI:[link/act]                                                                                                **
                                           **     FIBER:[link/at]                                                                                               **
                                           *************************************************************************/
    MARS_LED_MODE1,        /**   each port has 2 LED indicator symbols, {1st led, 2nd led}, to indicate:                 **
                                           **     MDI:[speed1000/act] [speed100(10)/act]                                                         **
                                           **     FIBER:[speed1000/act] [speed100/act]                                                            **
                                           *************************************************************************/
    MARS_LED_MODE2,        /**   each port has 3 LED indicator symbols, {1st led, 2nd led, 3rd led}, to indicate:     **
                                           **     MDI:[speed1000/act] [speed100/act] [speed10/act]                                         **
                                           **     FIBER:[speed1000/act] [speed100/act] [Disable]                                              **
                                           *************************************************************************/
    MARS_LED_MODE3,         /**   each port has 3 LED indicator symbols, {1st led, 2nd led, 3rd led}, to indicate:    **
                                           **     MDI:[link/act] [speed1000] [speed100]                                                            **
                                           **     FIBER:[link/act] [speed1000] [speed100]                                                         **
                                           *************************************************************************/
    MARS_LED_MAX,
};
typedef enum mars_led_mode_e mars_led_mode_t;

enum mars_fast_link_down_delay_e
{
    MARS_FAST_LINK_DOWN_DELAY_0MS,
    MARS_FAST_LINK_DOWN_DELAY_5MS,
    MARS_FAST_LINK_DOWN_DELAY_10MS,
    MARS_FAST_LINK_DOWN_DELAY_20MS,
    MARS_FAST_LINK_DOWN_DELAY_40MS,
    MARS_FAST_LINK_DOWN_DELAY_80MS,
    MARS_FAST_LINK_DOWN_DELAY_160MS,
    MARS_FAST_LINK_DOWN_DELAY_320MS,
};
typedef enum mars_fast_link_down_delay_e mars_fast_link_down_delay_t;

enum mars_packet_checker_stream_e
{
    MARS_PACKET_CHECKER_DOWNSTREAM,  /* copper port */
    MARS_PACKET_CHECKER_UPSTREAM,        /* qsgmii channel */
    MARS_PACKET_CHECKER_STREAM_MAX,
};
typedef enum mars_packet_checker_stream_e mars_packet_checker_stream_t;

enum mars_synce_freq_e
{
    MARS_SYNCE_FREQ_25MHZ,         /* output 25MHz syncE clock */
    MARS_SYNCE_FREQ_31P25MHZ,   /* output 31.25MHz syncE clock */
    MARS_SYNCE_FREQ_125MHZ,       /* output 125MHz syncE clock */
    MARS_LOCAL_FREQ_25MHZ,         /* output 25MHz reference clock */
};
typedef enum mars_synce_freq_e mars_synce_freq_t;

enum mars_mdi_mdix_e
{
    MARS_MDI_MDIX_AUTO,
    MARS_MANUAL_MDI,
    MARS_MANUAL_MDIX,
};
typedef enum mars_mdi_mdix_e mars_mdi_mdix_t;

enum mars_lds_result_e
{
    MARS_LDS_RESULT_DEFAULT,          /* not in lds mode */
    MARS_LDS_RESULT_2_PAIR_10M,
    MARS_LDS_RESULT_2_PAIR_100M,
    MARS_LDS_RESULT_1_PAIR_10M,
    MARS_LDS_RESULT_1_PAIR_100M,
    MARS_LDS_RESULT_4_PAIR_100M,
};
typedef enum mars_lds_result_e mars_lds_result_t;

enum mars_led_blink_duty_cycle_e
{
    MARS_LED_50_ON_50_OFF,
    MARS_LED_67_ON_33_OFF,
    MARS_LED_75_ON_25_OFF,
    MARS_LED_83_ON_17_OFF,
    MARS_LED_50_OFF_50_ON,
    MARS_LED_33_ON_67_OFF,
    MARS_LED_25_ON_75_OFF,
    MARS_LED_17_ON_83_OFF,
    MARS_LED_BLINK_MAX,
};
typedef enum mars_led_blink_duty_cycle_e mars_led_blink_duty_cycle_t;

enum mars_led_blink_freq_e
{
    MARS_LED_BLINK_FREQ_4HZ,
    MARS_LED_BLINK_FREQ_8HZ,
    MARS_LED_BLINK_FREQ_16HZ,
    MARS_LED_BLINK_FREQ_32HZ,
    MARS_LED_BLINK_FREQ_MAX,
};
typedef enum mars_led_blink_freq_e mars_led_blink_freq_t;

enum mars_led_port_e
{
    MARS_LED_PORT_MDI0,
    MARS_LED_PORT_MDI1,
    MARS_LED_PORT_MDI2,
    MARS_LED_PORT_MDI3,
    MARS_LED_PORT_MDI4_FIB0, /* fib for 4c */
    MARS_LED_PORT_MDI5_FIB1,
    MARS_LED_PORT_MDI6_FIB2,
    MARS_LED_PORT_MDI7_FIB3,
    MARS_LED_PORT_MAX,
};
typedef enum mars_led_port_e mars_led_port_t;

enum mars_remote_pair_e
{
    MARS_REMOTE_PAIR_ABSENT,    /* remote pair is absent */
    MARS_REMOTE_PAIR_PRESENT,       /* remote pair is present */
    MARS_REMOTE_PAIR_MAX
};
typedef enum mars_remote_pair_e mars_remote_pair_t;

enum mars_vct_status_e
{
    MARS_VCT_STATUS_CLOSED,     /* VCT Mod is not start */
    MARS_VCT_STATUS_RUNNING,        /* VCT Mod is running   */
    MARS_VCT_STATUS_FINISHED,       /* VCT Mod is finished  */
    MARS_VCT_STATUS_MAX,
};
typedef enum mars_vct_status_e mars_vct_status_t;

enum mars_pair_state_e
{
    MARS_PAIR_STATE_NORMAL,                /* Correctly terminated pair */
    MARS_PAIR_STATE_ABNORMAL_TERMINATION,  /* Abnormal termination */
    MARS_PAIR_STATE_ABNORMAL_SHORTED,      /* Short pair */
    MARS_PAIR_STATE_ABNORMAL_OPEN,         /* Open pair */
    MARS_PAIR_STATE_MAX
};
typedef enum mars_pair_state_e mars_pair_state_t;

struct mars_pair_info_s
{
    uint16 pair_length;
    mars_pair_state_t pair_status;
};
typedef struct mars_pair_info_s mars_pair_info_t;

struct mars_port_cable_info_s
{
    mars_pair_info_t pair_A;
    mars_pair_info_t pair_B;
    mars_pair_info_t pair_C;
    mars_pair_info_t pair_D;
};
typedef struct mars_port_cable_info_s mars_port_cable_info_t;

struct mars_lds_details_s
{
    uint32 linkup;
    uint32 length;
    uint32 result;
};
typedef struct mars_lds_details_s mars_lds_details_t;

struct mars_led_details_s
{
    uint16 act_low;                   /* control SLED's polarity. 1: active low; 0: active high */
    uint16 bit_mask;                /* The thress mask bit for the three LED pins of each port: 1'b1: enable the
                                                  pin output; 1'b0: disable pin output */
    uint16 port_en_ctrl ;          /* Control to enable the eight ports' SLED: 1'b1: enable serial led output for
                                                  this port; 1'b0: disable serial led output for this port */
    uint16 clk_en;                    /* 1: enable SLED clock to output to SLED_CK pin; 0: disable SLED clock
                                                  output and drive 0 on SLED_CK pin. */
    uint16 data_en;                  /* 1: enable SLED data to output to SLED_DA pin; 0: disable SLED data output
                                                  and drive 0 on SLED_DA pin */
    uint16 burst_cycle;            /* Serial led burst cycle. SLED status will be updated when the timer is done.
                                                  2'b00: 8ms 2'b01: 16ms 2'b10: 32ms 2'b11: 64ms */
    uint16 clk_cycle;               /* Serial led clock cycle:
                                                  2'b00: 80ns 2'b01: 160ns 2'b10: 240ns 2'b11: 320ns */
};
typedef struct mars_led_details_s mars_led_details_t;

struct mars_led_serial_s
{
    uint16 port_num;
    uint16 led_id;   /* 0x0:led0; 0x1:led1; 0x2:led2; 0x3:not used */
};
typedef struct mars_led_serial_s mars_led_serial_t;

/* Begin, used for ctc_phy_mars8p_set_led_blink() */
#define MARS_LED_FIBER_PORT   (1U<<20)     /* for 4c, fiber port */
#define MARS_LED2_FORCE_EN   (1U<<19)
#define MARS_LED1_FORCE_EN   (1U<<18)
#define MARS_LED0_FORCE_EN   (1U<<17)

#define MARS_LED_NUM_2       (1U<<16)        /* to set/get led2 blink setting */
#define MARS_LED_NUM_1       (1U<<15)        /* to set/get led1 blink setting */
#define MARS_LED_NUM_0       (1U<<14)        /* to set/get led0 blink setting */

#define MARS_LED_ACT_BLK_IND   (1U<<13)    /* When traffic is present, make LED1 BLINK no matter the previous LED status is
                                                               ON or OFF, or make LED1 blink only when the previous LED is ON. */
#define MARS_LED_FDX_ON_EN       (1U<<12)  /* 1: If BLINK status is not activated, when PHY link up and duplex mode is full duplex, LED will be ON. */
#define MARS_LED_HDX_ON_EN       (1U<<11)   /* If BLINK status is not activated, when PHY link up and duplex mode is half duplex. */
#define MARS_LED_TXACT_BLK_EN  (1U<<10)  /* 1: If LED_ACT_BLK_IND is 1, or LED_ACT_BLK_IND is 0 and ON at certain speed or
                                                             duplex more is/are activated, when PHY link up and TX is active. */
#define MARS_LED_RXACT_BLK_EN  (1U<<9)   /* If LED_ACT_BLK_IND is 1, or LED_ACT_BLK_IND is 0 and ON at certain speed or
                                                             duplex more is/are activated, when PHY link up and RX is active */
#define MARS_LED_TXACT_ON_EN   (1U<<8)   /* 1 = if BLINK status is not activated, when PHY link up and TX is active, make LED1 ON at least 10ms */
#define MARS_LED_RXACT_ON_EN   (1U<<7)   /* 1 = if BLINK status is not activated, when PHY link up and RX is active, make LED1 ON at least 10ms */
#define MARS_LED_GT_ON_EN         (1U<<6)   /* 1 = if BLINK status is not activated, when PHY link up and speed mode is 1000Base-T, make LED1 ON */
#define MARS_LED_HT_ON_EN         (1U<<5)  /* 1 = if BLINK status is not activated, when PHY link up and speed mode is 100Base_TX, make LED1 ON; */
#define MARS_LED_BT_ON_EN         (1U<<4)  /* 1 = if BLINK status is not activated, when PHY link up and speed mode is 10Base-T, make LED1 ON */
#define MARS_LED_COL_BLK_EN      (1U<<3)  /* 1 = if PHY link up and collision happen, make LED1 BLINK */
#define MARS_LED_GT_BLK_EN        (1U<<2)  /* 1 = if PHY link up and speed mode is 1000Base-T, make LED1 BLINK */
#define MARS_LED_HT_BLK_EN        (1U<<1)  /* 1 = if PHY link up and speed mode is 100Base-T, make LED1 BLINK */
#define MARS_LED_BT_BLK_EN        (1U<<0)  /* 1 = if PHY link up and speed mode is 100Base-T, make LED1 BLINK */

#define MARS_LED_BLK_MASK     0x3fff
/* End */

struct mars_led_blink_act_s
{
    uint16 led_blk_duty_cycle;
    uint16 led_blk_freq;
};
typedef struct mars_led_blink_act_s mars_led_blink_act_t;

struct mars_synce_s
{
    uint16 channel;
    uint16 enable;
    uint16 freq;
};
typedef struct mars_synce_s mars_synce_t;

struct mars_prbs_result_s
{
    uint32 prbs;
    uint32 sync;  /* real time PRBS test synchronization status */
    uint32 error;  /* real time received error bit counter */
};
typedef struct mars_prbs_result_s mars_prbs_result_t;

struct mars_packet_generator_count_s
{
    mars_packet_checker_stream_t side;
    uint32 rx_good;
    uint16 rx_error;
    uint32 tx_good;
    uint16 tx_error;
};
typedef struct mars_packet_generator_count_s mars_packet_generator_count_t;

struct mars_packet_generator_s
{
    uint16 packet_num;  /* the number of packets, 0 means continuous packet */
    uint16 packet_len;    /* packet length */
    uint16 addr_en;         /* enable address setting */
    uint16 addr_da;         /* the last byte of destination address */
    uint16 addr_sa;         /* the last byte of source address */
};
typedef struct mars_packet_generator_s mars_packet_generator_t;

struct mars_link_status_s
{
    uint32 speed_status;           /**< port speed status */
    uint32 duplex_status;         /**< port duplex status */
    uint32 auto_neg_en;           /**< port auto-nego enable */
    uint32 link_up;                    /**< port link status */
    uint32 qsg_link_up;            /**< qsgmii link status */
    uint32 qsg_speed_status;  /**< qsgmii speed status */
    uint32 sg_link_up;              /**< sgmii/fiber link status */
    uint32 sg_speed_status;    /**< sgmii/fiber speed status */
};
typedef struct mars_link_status_s mars_link_status_t;
