#ifndef __BMS_IRQ_XCVRD_H__
#define __BMS_IRQ_XCVRD_H__

/* these defines need to be 0*/
#define INTR_MASK_EN 0
#define INTR_STATUS_EN 0
#define MODSEL_EN 0
#define RST_EN 0
#define PRESENT_EN 0
#define INIT_DONE_DIS 0
#define LPMODE_DIS 0

typedef int (*isr_t)(unsigned int, char*, mqd_t);
typedef void* (*isrd_t)(void*);

typedef struct {
    unsigned int port_num;
    char *present;
    char *intr_src;
    char *intr_msk;
    char *modsel;
    char *reset;
    char *lpmode;
    char *mq_name;
    mqd_t mq_desc;
    isr_t isr;
    pthread_t isrd_tid;
    isrd_t isrd;
    unsigned char smbus_num;
} bms_xcvr_serv_data_t;

typedef struct {
    unsigned char intr_type;
#define INTR_TYPE_RX_INTR 1 /* Receving an interrupt */
    unsigned int port_bmap;
} bms_xcvr_serv_mq_data_t;

enum {
    XCVR_PRESENT = 0,
    XCVR_MODSEL,
    XCVR_RESET,
    XCVR_INTR_MSK,
    XCVR_INTR_SRC,
    XCVR_INIT_DONE,
    XCVR_LPMODE,
};

extern bms_xcvr_serv_data_t xcvrirq_data[];
extern int xcvrirq_data_num;
extern pthread_mutex_t bms_xcvr_data_lock;
extern char bms_xcvr_bmap_to_num_str[];

extern int bms_xcvr_pin_read(char *filename, unsigned int *value);
extern void bms_xcvr_data_read(int pin_name, unsigned int *value);
extern void bms_xcvr_data_write(int pin_name, unsigned int value);
extern int bms_xcvr_pin_bmap_write(int pin_name, unsigned int value);
extern int bms_xcvr_pin_bmap_modify(int pin_num, unsigned int value, unsigned int old_value);
extern void bms_xcvr_bmap_modify(unsigned int *changed_bmap, unsigned int check_bmap, unsigned int enable_disable);
extern void bms_xcvr_bmap_to_num(unsigned int bmap);

#endif /* __BMS_IRQ_XCVRD_H__ */
