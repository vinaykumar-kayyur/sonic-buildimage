/*
 * Copyright 2019 Broadcom. All rights reserved.
 * The term “Broadcom” refers to Broadcom Inc. and/or its subsidiaries.
 *
 * A pddf kernel module to manage various LEDs of a switch
 */

#include <linux/kobject.h>
#include <linux/string.h>
#include <linux/sysfs.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/hwmon-sysfs.h>
#include "pddf_led_defs.h"
#include "pddf_client_defs.h"
#include <linux/err.h>
#include <linux/mutex.h>
#include <linux/slab.h>

#define DEBUG 1
LED_OPS_DATA sys_led_ops_data[1]={0};
LED_OPS_DATA* psu_led_ops_data=NULL;
LED_OPS_DATA diag_led_ops_data[1]= {0};
LED_OPS_DATA fan_led_ops_data[1]= {0};
LED_OPS_DATA loc_led_ops_data[1]= {0};
LED_OPS_DATA* fantray_led_ops_data=NULL;
LED_OPS_DATA temp_data={0};
LED_OPS_DATA* dev_list[LED_TYPE_MAX] = {
	sys_led_ops_data,
	NULL,
	fan_led_ops_data,
	NULL,
	diag_led_ops_data,
	loc_led_ops_data,
	NULL
};
int num_psus = 0;
int num_fans = 0;

extern int board_i2c_cpld_read(unsigned short cpld_addr, u8 reg);
extern int board_i2c_cpld_write(unsigned short cpld_addr, u8 reg, u8 value);
extern ssize_t show_pddf_data(struct device *dev, struct device_attribute *da, char *buf);
extern ssize_t store_pddf_data(struct device *dev, struct device_attribute *da, const char *buf, size_t count);

static LED_TYPE get_dev_type(char* name)
{
        LED_TYPE ret = LED_TYPE_MAX;
        if(strcasecmp(name, "SYS_LED")==0) {
                ret = LED_SYS;
        } else if(strcasecmp(name, "FAN_LED")==0) {
                ret = LED_FAN;
        } else if(strstr(name, "PSU_LED")) {
                ret = LED_PSU;
        } else if(strcasecmp(name, "DIAG_LED")==0) {
                ret = LED_DIAG;
        } else if(strcasecmp(name, "LOC_LED")==0) {
                ret = LED_LOC;
        } else if(strstr(name, "FANTRAY_LED")) {
                ret = LED_FANTRAY;
        }
#if DEBUG > 1
        pddf_dbg(LED, KERN_INFO "LED get_dev_type: %s; %d\n", name, ret);
#endif
        return (ret);
}
static int dev_index_check(LED_TYPE type, int index)
{
#if DEBUG
	pddf_dbg(LED, "dev_index_check: type:%s index:%d num_psus:%d num_fans:%d\n", 
		LED_TYPE_STR[type], index, num_psus, num_fans);
#endif
        switch(type)
        {
                case LED_PSU:
                        if(index >= num_psus) return (-1);
                break;
                case LED_FANTRAY:
                        if(index >= num_fans) return (-1);
                break;
                default:
                        if(index >= 1) return (-1);
                break;
        }
        return (0);
}

static LED_OPS_DATA* find_led_ops_data(struct device_attribute *da)
{
        struct pddf_data_attribute *_ptr = (struct pddf_data_attribute *)da;
        LED_OPS_DATA* ptr=(LED_OPS_DATA*)_ptr->addr;
        LED_TYPE led_type;
        if(!ptr || strlen(ptr->device_name)==0 ) return(NULL);


        if((led_type=get_dev_type(ptr->device_name))==LED_TYPE_MAX) {
                printk(KERN_ERR "PDDF_LED ERROR *%s Unsupported Led Type\n", __func__);
                return(NULL);
        }
        if(dev_index_check(led_type, ptr->index)==-1) {
                printk(KERN_ERR "PDDF_LED ERROR %s invalid index: %d for type:%s\n", __func__, ptr->index, ptr->device_name);
                return(NULL);
        }
#if DEBUG
        pddf_dbg(LED, "find_led_ops_data: name:%s; index=%d tempAddr:%p actualAddr:%p\n",
                                ptr->device_name, ptr->index, ptr, dev_list[led_type]+ptr->index);
#endif
        return (dev_list[led_type]+ptr->index);
}

static void print_led_data(LED_OPS_DATA *ptr)
{
	if(!ptr) return ;
	pddf_dbg(LED, KERN_INFO "Print %s index:%d num_psus:%d num_fans:%d ADDR=%p\n", 
					ptr->device_name, ptr->index, num_psus, num_fans, ptr);
	pddf_dbg(LED, KERN_INFO "\tindex: %d\n", ptr->index); 
	pddf_dbg(LED, KERN_INFO  "\tcur_state: %d; %s; %s\n", ptr->cur_state.state, ptr->cur_state.color, ptr->cur_state.color_state); 
	if(ptr->data[ON].swpld_addr) {
		pddf_dbg(LED, KERN_INFO "\t\t[ON]: addr/offset:0x%x;0x%x color:%s; value:%x; mask_bits: 0x%x; pos:%d\n", 
		ptr->data[ON].swpld_addr, ptr->data[ON].swpld_addr_offset,
		ptr->data[ON].color, ptr->data[ON].value, ptr->data[ON].bits.mask_bits, ptr->data[ON].bits.pos); 
	}

	if(ptr->data[OFF].swpld_addr) {
		pddf_dbg(LED, KERN_INFO  "\t\t[OFF]: addr/offset:0x%x;0x%x  color:%s; value:%x; mask_bits: 0x%x; pos:%d\n", 
		ptr->data[OFF].swpld_addr, ptr->data[OFF].swpld_addr_offset,
		ptr->data[OFF].color, ptr->data[OFF].value, ptr->data[OFF].bits.mask_bits, ptr->data[OFF].bits.pos); 
	}

	if(ptr->data[FAULTY].swpld_addr) {
		pddf_dbg(LED, KERN_INFO "\t\t[FAULTY]: addr/offset:0x%x;0x%x  color:%s; value:%x; mask_bits: 0x%x; pos:%d\n", 
		ptr->data[FAULTY].swpld_addr, ptr->data[FAULTY].swpld_addr_offset,
		ptr->data[FAULTY].color, ptr->data[FAULTY].value, ptr->data[FAULTY].bits.mask_bits, ptr->data[FAULTY].bits.pos); 
	}

	if(ptr->data[BLINK].swpld_addr) {
		pddf_dbg(LED, KERN_INFO "\t\t[BLINK]: addr/offset:0x%x;0x%x  color:%s; value:%x; mask_bits: 0x%x; pos:%d\n", 
		ptr->data[BLINK].swpld_addr, ptr->data[BLINK].swpld_addr_offset,
		ptr->data[BLINK].color, ptr->data[BLINK].value, ptr->data[BLINK].bits.mask_bits, ptr->data[BLINK].bits.pos); 
	}
}
	
ssize_t get_status_led(struct device_attribute *da)
{
	int ret=0;
	struct pddf_data_attribute *_ptr = (struct pddf_data_attribute *)da;
	LED_OPS_DATA* temp_data_ptr=(LED_OPS_DATA*)_ptr->addr;
	LED_OPS_DATA* ops_ptr=find_led_ops_data(da);
	uint32_t color_val=0, sys_val=0;
	int state=0;
	if (!ops_ptr) { 
		printk(KERN_ERR "PDDF_LED ERROR %s: Cannot find LED Ptr", __func__);
		return (-1);
	}
	if (ops_ptr->swpld_addr == 0x0) {
		printk(KERN_ERR "PDDF_LED ERROR %s: device: %s %d not configured\n", __func__,
			temp_data_ptr->device_name, temp_data_ptr->index);
		return (-1);
	}
    sys_val = board_i2c_cpld_read(ops_ptr->swpld_addr, ops_ptr->swpld_addr_offset);
	if (sys_val < 0)
		return sys_val;

	strcpy(temp_data.cur_state.color_state, "None"); 
	strcpy(temp_data.cur_state.color, "None"); 
	for (state=0; state<MAX_LED_STATUS; state++) {
        	color_val = (sys_val & ~ops_ptr->data[state].bits.mask_bits);
		if ((color_val ^ (ops_ptr->data[state].value<<ops_ptr->data[state].bits.pos))==0) {
			if(state == BLINK)
				strcpy(temp_data.cur_state.color_state,"Blink"); 
			else {
				strcpy(temp_data.cur_state.color, ops_ptr->data[state].color);
        			if(strcasecmp(ops_ptr->data[state].color, "off")==0) {
					strcpy(temp_data.cur_state.color_state, ""); 
				} else {
					strcpy(temp_data.cur_state.color_state, "Solid"); 
				}
			}
		}
	}
#if DEBUG
        pddf_dbg(LED, KERN_ERR "Get : %s:%d addr/offset:0x%x; 0x%x value=0x%x [%s:%s]\n",
		ops_ptr->device_name, ops_ptr->index, 
                ops_ptr->swpld_addr, ops_ptr->swpld_addr_offset, sys_val, 
		temp_data.cur_state.color, temp_data.cur_state.color_state);
#endif
	return(ret);	
}

ssize_t set_status_led(struct device_attribute *da)
{
	int ret=0;
	uint32_t sys_val=0, new_val=0;
	int cur_state = 0;
	struct pddf_data_attribute *_ptr = (struct pddf_data_attribute *)da;
	LED_OPS_DATA* temp_data_ptr=(LED_OPS_DATA*)_ptr->addr;
	LED_OPS_DATA* ops_ptr=find_led_ops_data(da);
	char* _buf=temp_data_ptr->cur_state.color;
	int blink=0;

	if (!ops_ptr) { 
		printk(KERN_ERR "PDDF_LED ERROR %s: Cannot find LED Ptr", __func__);
		return (-1);
	}
	if (ops_ptr->swpld_addr == 0x0) {
		printk(KERN_ERR "PDDF_LED ERROR %s: device: %s %d not configured\n",
			__func__, ops_ptr->device_name, ops_ptr->index);
		return (-1);
	}
#if DEBUG
	pddf_dbg(LED, KERN_ERR "%s: Set [%s;%d] color[%s;%s]\n", __func__,
		temp_data_ptr->device_name, temp_data_ptr->index,
		temp_data_ptr->cur_state.color, temp_data_ptr->cur_state.color_state);
#endif
        if(strcasecmp(_buf, "on")==0) {
                cur_state = ON;
        } else if(strcasecmp(_buf, "off")==0) {
                cur_state=OFF;
        } else if(strcasecmp(_buf, "faulty")==0) {
                cur_state=FAULTY;
        } else {
                printk(KERN_ERR "PDDF_LED ERROR %s: not supported: %s\n", _buf, __func__);
                return (-1);
        }
	if(ops_ptr->data[cur_state].swpld_addr != 0x0) {
        	sys_val = board_i2c_cpld_read(ops_ptr->swpld_addr, ops_ptr->swpld_addr_offset);
			if (sys_val < 0)
				return sys_val;

        	new_val = (sys_val & ops_ptr->data[cur_state].bits.mask_bits) |
                                (ops_ptr->data[cur_state].value << ops_ptr->data[cur_state].bits.pos);

        		if(strcasecmp(temp_data_ptr->cur_state.color_state, "blink")==0) {
				if (ops_ptr->data[BLINK].swpld_addr != 0x0) {
        				new_val = (new_val & ops_ptr->data[BLINK].bits.mask_bits) |
                                		(ops_ptr->data[BLINK].value << ops_ptr->data[BLINK].bits.pos);
					blink=1;
				} else {
					printk(KERN_ERR "PDDF_LED ERROR %s: %s %d BLINK is not supported\n",__func__,
						ops_ptr->device_name, ops_ptr->index);
					return (-1);
				}
			}
	} else {
		printk(KERN_ERR "PDDF_LED ERROR %s: %s %d state %d; %s not configured\n",__func__, 
			ops_ptr->device_name, ops_ptr->index, cur_state, _buf);
		return (-1);
	}

        board_i2c_cpld_write(ops_ptr->swpld_addr, ops_ptr->swpld_addr_offset, new_val);
#if DEBUG
        pddf_dbg(LED, "Set state:%s;%s;%s 0x%x:0x%x sys_val:0x%x new_val:0x%x read:0x%x\n",
		LED_TYPE_STR[cur_state], ops_ptr->data[cur_state].color, blink? "Blink":"Solid",
                ops_ptr->swpld_addr, ops_ptr->swpld_addr_offset,
                sys_val, new_val,
		ret = board_i2c_cpld_read(ops_ptr->swpld_addr, ops_ptr->swpld_addr_offset));
		if (ret < 0)
		{
			printk(KERN_ERR "PDDF_LED ERROR %s: Error %d in reading from cpld(0x%x) offset 0x%x\n", __FUNCTION__, ret, ops_ptr->swpld_addr, ops_ptr->swpld_addr_offset);
			return ret;
		}
#endif
	return(ret);
}


ssize_t show_pddf_data(struct device *dev, struct device_attribute *da,
             char *buf)
{
        int ret = 0;
        struct pddf_data_attribute *ptr = (struct pddf_data_attribute *)da;
        switch(ptr->type)
        {
                case PDDF_CHAR:
                        ret = sprintf(buf, "%s\n", ptr->addr);
                        break;
                case PDDF_INT_DEC:
                        ret = sprintf(buf, "%d\n", *(int*)(ptr->addr));
                        break;
                case PDDF_INT_HEX:
                        ret = sprintf(buf, "0x%x\n", *(int*)(ptr->addr));
                        break;
                case PDDF_USHORT:
                        ret = sprintf(buf, "0x%x\n", *(unsigned short *)(ptr->addr));
                        break;
                case PDDF_UINT32:
                        ret = sprintf(buf, "0x%x\n", *(uint32_t *)(ptr->addr));
                        break;
                default:
                        break;
        }
#if DEBUG 
        pddf_dbg(LED, "[ READ ] DATA ATTR PTR [%s] TYPE:%d, Value:[%s]\n", 
		ptr->dev_attr.attr.name, ptr->type, buf);
#endif
        return ret;
}

ssize_t store_pddf_data(struct device *dev, struct device_attribute *da, const char *buf, size_t count)
{
        int ret = 0, num = 0;
        //pddf_dbg(KERN_ERR "%s: %s", __FUNCTION__, buf);
        struct pddf_data_attribute *ptr = (struct pddf_data_attribute *)da;
        switch(ptr->type)
        {
                case PDDF_CHAR:
                        strncpy(ptr->addr, buf, strlen(buf)-1); // to discard newline char form buf
                        ptr->addr[strlen(buf)-1] = '\0';
#if DEBUG
        		pddf_dbg(LED, KERN_ERR "[ WRITE ] ATTR PTR [%s] PDDF_CHAR  VALUE:%s\n", 
				ptr->dev_attr.attr.name, ptr->addr);
#endif
                        break;
                case PDDF_INT_DEC:
                        ret = kstrtoint(buf,10,&num);
                        if (ret==0)
                                *(int *)(ptr->addr) = num;
#if DEBUG
        		pddf_dbg(LED, KERN_ERR "[ WRITE ] ATTR PTR [%s] PDDF_DEC  VALUE:%d\n", 
				ptr->dev_attr.attr.name, *(int *)(ptr->addr));
#endif
                        break;
                case PDDF_INT_HEX:
                        ret = kstrtoint(buf,16,&num);
                        if (ret==0)
                                *(int *)(ptr->addr) = num;
#if DEBUG
        		pddf_dbg(LED, KERN_ERR "[ WRITE ] ATTR PTR [%s] PDDF_HEX  VALUE:0x%x\n", 
				ptr->dev_attr.attr.name, *(int *)(ptr->addr));
#endif
                        break;
                case PDDF_USHORT:
                        ret = kstrtoint(buf,16,&num);
                        if (ret==0)
                                *(unsigned short *)(ptr->addr) = (unsigned short)num;
#if DEBUG
        		pddf_dbg(LED, KERN_ERR "[ WRITE ] ATTR PTR [%s] PDDF_USHORT  VALUE:%x\n", 
				ptr->dev_attr.attr.name, *(unsigned short *)(ptr->addr));
#endif
                        break;
                case PDDF_UINT32:
                        ret = kstrtoint(buf,16,&num);
                        if (ret==0)
                                *(uint32_t *)(ptr->addr) = (uint32_t)num;
#if DEBUG
        		pddf_dbg(LED, KERN_ERR "[ WRITE ] ATTR PTR [%s] PDDF_UINT32 VALUE:%d\n", 
				ptr->dev_attr.attr.name, *(uint32_t *)(ptr->addr));
#endif
                        break;
                default:
                        break;
        }
        return count;
}

static int load_led_ops_data(struct device_attribute *da, LED_STATUS state)
{
	struct pddf_data_attribute *_ptr = (struct pddf_data_attribute *)da;
	LED_OPS_DATA* ptr=(LED_OPS_DATA*)_ptr->addr;
	LED_TYPE led_type;
	LED_OPS_DATA* ops_ptr=NULL;
	if(!ptr || strlen(ptr->device_name)==0 ) return(-1); 
#if DEBUG
	if(ptr->device_name) pddf_dbg(LED, "SYSTEM_LED: load_led_ops_data: name:%s; index=%d ADDR=%p\n", 
						ptr->device_name, ptr->index, ptr); 
#endif
	if((led_type=get_dev_type(ptr->device_name))==LED_TYPE_MAX) {
		printk(KERN_ERR "PDDF_LED ERROR *%s Unsupported Led Type\n", __func__);
		return(-1);
	}
	if(dev_index_check(led_type, ptr->index)==-1) {
		printk(KERN_ERR "PDDF_LED ERROR %s invalid index: %d for type:%d\n", __func__, ptr->index, led_type);
		return(-1);
	}
	ops_ptr = dev_list[led_type]+ptr->index;

	memcpy(ops_ptr->device_name, ptr->device_name, sizeof(ops_ptr->device_name));
	ops_ptr->index = ptr->index;
	memcpy(&ops_ptr->data[state], &ptr->data[state], sizeof(LED_DATA));
	ops_ptr->data[state].swpld_addr = ptr->swpld_addr;
	ops_ptr->data[state].swpld_addr_offset = ptr->swpld_addr_offset;
	ops_ptr->swpld_addr = ptr->swpld_addr;
	ops_ptr->swpld_addr_offset = ptr->swpld_addr_offset;
#if DEBUG
	print_led_data(ptr);
	print_led_data(dev_list[led_type]+ptr->index);
#endif
	memset(ptr, 0, sizeof(LED_OPS_DATA));
	return (0);
}

static int show_led_ops_data(struct device_attribute *da)
{
        LED_OPS_DATA* ops_ptr=find_led_ops_data(da);
        print_led_data(ops_ptr);
	return(0);
}

static int verify_led_ops_data(struct device_attribute *da)
{
	struct pddf_data_attribute *_ptr = (struct pddf_data_attribute *)da;
	LED_OPS_DATA* ptr=(LED_OPS_DATA*)_ptr->addr;
	LED_OPS_DATA* ops_ptr=find_led_ops_data(da);

	if(ops_ptr) 
		memcpy(ptr, ops_ptr, sizeof(LED_OPS_DATA));
	else 
		pddf_dbg(LED, "SYSTEM_LED: verify_led_ops_data: Failed to find ops_ptr name:%s; index=%d\n", ptr->device_name, ptr->index);
	return (0);
}

ssize_t dev_operation(struct device *dev, struct device_attribute *da, const char *buf, size_t count)
{
	if(strncmp(buf, "create_on", strlen("create_on"))==0 ) {
		load_led_ops_data(da, ON);
	}
	else if(strncmp(buf, "create_off", strlen("create_off"))==0 ) {
		load_led_ops_data(da, OFF);
	}
	else if(strncmp(buf, "create_faulty", strlen("create_faulty"))==0 ) {
		load_led_ops_data(da, FAULTY);
	}
	else if(strncmp(buf, "create_blink", strlen("create_blink"))==0 ) {
		load_led_ops_data(da, BLINK);
	}
	else if(strncmp(buf, "show", strlen("show"))==0 ) {
		show_led_ops_data(da);
	}
	else if(strncmp(buf, "verify", strlen("verify"))==0 ) {
		verify_led_ops_data(da);
	}
	else if(strncmp(buf, "get_status", strlen("get_status"))==0 ) {
		get_status_led(da);
	}
	else if(strncmp(buf, "set_status", strlen("set_status"))==0 ) {
		set_status_led(da);
	}
	else {
		printk(KERN_ERR "PDDF_ERROR %s: Invalid value for dev_ops %s", __FUNCTION__, buf);
	}
	return(count);
}

ssize_t store_config_data(struct device *dev, struct device_attribute *da, const char *buf, size_t count)
{
	int ret, num;
	struct pddf_data_attribute *ptr = (struct pddf_data_attribute *)da;
	if(strncmp(ptr->dev_attr.attr.name, "num_psus", strlen("num_psus"))==0 ) {
	       ret = kstrtoint(buf,10,&num);
               if (ret==0)
                      *(int *)(ptr->addr) = num;
	       if(psu_led_ops_data == NULL) { 
	       		if ((psu_led_ops_data = kzalloc(num * sizeof(LED_OPS_DATA), GFP_KERNEL)) == NULL) {
				printk(KERN_ERR "PDDF_LED ERROR failed to allocate memory for PSU LED\n");
				return (count);
	       		}
			pddf_dbg(LED, "Allocate PSU LED Memory ADDR=%p\n", psu_led_ops_data);
			dev_list[LED_PSU]=psu_led_ops_data;
		}
#if DEBUG
        pddf_dbg(LED, "[ WRITE ] ATTR CONFIG [%s] VALUE:%d; %d\n",
                        ptr->dev_attr.attr.name, num, num_psus);
#endif
		return(count);
	}
        if(strncmp(ptr->dev_attr.attr.name, "num_fans", strlen("num_fans"))==0 ) {
               ret = kstrtoint(buf,10,&num);
               if (ret==0)
                      *(int *)(ptr->addr) = num;
	       if (fantray_led_ops_data == NULL) {
               		if ((fantray_led_ops_data = kzalloc(num * sizeof(LED_OPS_DATA), GFP_KERNEL)) == NULL) {
                        	printk(KERN_ERR "PDDF_LED ERROR failed to allocate memory for FANTRAY LED\n");
                        	return (count);
			}
			pddf_dbg(LED, "Allocate FanTray LED Memory ADDR=%p\n", fantray_led_ops_data);
			dev_list[LED_FANTRAY]=fantray_led_ops_data;
               }
#if DEBUG
        pddf_dbg(LED, "[ WRITE ] ATTR CONFIG [%s] VALUE:%d; %d\n",
                        ptr->dev_attr.attr.name, num, num_fans);
#endif
                return(count);
        }
        return (count);
}

ssize_t store_bits_data(struct device *dev, struct device_attribute *da, const char *buf, size_t count)
{
	int len = 0, num1 = 0, num2 = 0;
	char mask=0xFF;
	char *pptr=NULL;
	char bits[NAME_SIZE];
	struct pddf_data_attribute *ptr = (struct pddf_data_attribute *)da;
	MASK_BITS* bits_ptr=(MASK_BITS*)(ptr->addr); 
	strncpy(bits_ptr->bits, buf, strlen(buf)-1); // to discard newline char form buf
	bits_ptr->bits[strlen(buf)-1] = '\0';
	if((pptr=strstr(buf,":")) != NULL) {
		len=pptr-buf;
		sprintf(bits, buf);
		bits[len]='\0'; 	
		kstrtoint(bits,16,&num1);
                mask = mask & ~(1 << num1);
		sprintf(bits, ++pptr);
		kstrtoint(bits,16,&num2);
                bits_ptr->mask_bits = mask & ~(1 << num2);
                bits_ptr->pos = num2;
	} else {
		kstrtoint(buf,16,&num1);
                bits_ptr->mask_bits = mask & ~(1 << num1);
                bits_ptr->pos = num1;
	}
#if DEBUG
        pddf_dbg(LED, KERN_ERR "[ WRITE ] ATTR PTR Bits [%s] VALUE:%s mask:0x%x; pos:0x%x\n", 
			ptr->dev_attr.attr.name, bits_ptr->bits, bits_ptr->mask_bits, bits_ptr->pos);
#endif
	return (count);
}

/**************************************************************************
 * platform/ attributes 
 **************************************************************************/
PDDF_LED_DATA_ATTR(platform, num_psus, S_IWUSR|S_IRUGO, show_pddf_data, 
                store_config_data, PDDF_INT_DEC, sizeof(int), (void*)&num_psus); 
PDDF_LED_DATA_ATTR(platform, num_fans, S_IWUSR|S_IRUGO, show_pddf_data, 
                store_config_data, PDDF_INT_DEC, sizeof(int), (void*)&num_fans); 

struct attribute* attrs_platform[]={
                &pddf_dev_platform_attr_num_psus.dev_attr.attr,
                &pddf_dev_platform_attr_num_fans.dev_attr.attr,
                NULL,
};
struct attribute_group attr_group_platform={
                .attrs = attrs_platform,
};

/**************************************************************************
 * led/ attributes 
 **************************************************************************/
PDDF_LED_DATA_ATTR(dev, device_name, S_IWUSR|S_IRUGO, show_pddf_data, 
                store_pddf_data, PDDF_CHAR, NAME_SIZE, (void*)&temp_data.device_name); 
PDDF_LED_DATA_ATTR(dev, index, S_IWUSR|S_IRUGO, show_pddf_data, 
                store_pddf_data, PDDF_INT_DEC, sizeof(int), (void*)&temp_data.index); 
PDDF_LED_DATA_ATTR(dev, swpld_addr, S_IWUSR|S_IRUGO, show_pddf_data, 
                store_pddf_data, PDDF_INT_HEX, sizeof(int), (void*)&temp_data.swpld_addr); 
PDDF_LED_DATA_ATTR(dev, swpld_addr_offset, S_IWUSR|S_IRUGO, show_pddf_data, 
                store_pddf_data, PDDF_INT_HEX, sizeof(int), (void*)&temp_data.swpld_addr_offset); 
PDDF_LED_DATA_ATTR(dev, dev_ops , S_IWUSR, NULL,  
                dev_operation, PDDF_CHAR, NAME_SIZE, (void*)&temp_data);  

struct attribute* attrs_dev[]={ 
                &pddf_dev_dev_attr_device_name.dev_attr.attr, 
                &pddf_dev_dev_attr_index.dev_attr.attr, 
                &pddf_dev_dev_attr_swpld_addr.dev_attr.attr, 
                &pddf_dev_dev_attr_swpld_addr_offset.dev_attr.attr, 
                &pddf_dev_dev_attr_dev_ops.dev_attr.attr, 
                NULL,
}; 
struct attribute_group attr_group_dev={ 
                .attrs = attrs_dev, 
}; 

/**************************************************************************
 * on/, off/, faulty/, blink/ attributes 
 **************************************************************************/
#define LED_DEV_STATE_ATTR_GROUP(name, func) \
	PDDF_LED_DATA_ATTR(name, bits, S_IWUSR|S_IRUGO, show_pddf_data, \ 
		store_bits_data, PDDF_CHAR, NAME_SIZE, func.bits.bits); \
	PDDF_LED_DATA_ATTR(name, color, S_IWUSR|S_IRUGO, show_pddf_data, \
                store_pddf_data, PDDF_CHAR, NAME_SIZE, func.color); \
	PDDF_LED_DATA_ATTR(name, value, S_IWUSR|S_IRUGO, show_pddf_data, \
                store_pddf_data, PDDF_USHORT, sizeof(unsigned short), func.value); \
	struct attribute* attrs_##name[]={ \
		&pddf_dev_##name##_attr_bits.dev_attr.attr, \
        	&pddf_dev_##name##_attr_color.dev_attr.attr, \
        	&pddf_dev_##name##_attr_value.dev_attr.attr, \
        	NULL, \
	}; \
	struct attribute_group attr_group_##name={ \
        	.attrs = attrs_##name, \
	}; \


LED_DEV_STATE_ATTR_GROUP(on, (void*)&temp_data.data[ON])
LED_DEV_STATE_ATTR_GROUP(off, (void*)&temp_data.data[OFF])
LED_DEV_STATE_ATTR_GROUP(faulty, (void*)&temp_data.data[FAULTY])
LED_DEV_STATE_ATTR_GROUP(blink, (void*)&temp_data.data[BLINK])

/**************************************************************************
 * cur_state/ attributes 
 **************************************************************************/
PDDF_LED_DATA_ATTR(cur_state, color, S_IWUSR|S_IRUGO, show_pddf_data, 
                store_pddf_data, PDDF_CHAR, NAME_SIZE, (void*)&temp_data.cur_state.color); 
PDDF_LED_DATA_ATTR(cur_state, color_state, S_IWUSR|S_IRUGO, show_pddf_data, 
                store_pddf_data, PDDF_CHAR, NAME_SIZE, (void*)&temp_data.cur_state.color_state); 

struct attribute* attrs_cur_state[]={
                &pddf_dev_cur_state_attr_color.dev_attr.attr,
                &pddf_dev_cur_state_attr_color_state.dev_attr.attr,
                NULL,
};
struct attribute_group attr_group_cur_state={
                .attrs = attrs_cur_state,
};

/*************************************************************************/
#define KOBJ_FREE(obj) \
	if(obj) kobject_put(obj); \

void free_kobjs(void)
{
        KOBJ_FREE(cur_state_kobj)
        KOBJ_FREE(faulty_kobj)
        KOBJ_FREE(blink_kobj)
        KOBJ_FREE(off_kobj)
        KOBJ_FREE(on_kobj)
        KOBJ_FREE(led_kobj)
        KOBJ_FREE(platform_kobj)
}

int KBOJ_CREATE(char* name, struct kobject* parent, struct kobject** child)
{
	if (parent) {
        	*child = kobject_create_and_add(name, parent); 
	} else {
		printk(KERN_ERR "PDDF_LED ERROR to create %s kobj; null parent\n", name);
                free_kobjs(); 
                return (-ENOMEM); 
	}
	return (0);
}

int LED_DEV_ATTR_CREATE(struct kobject *kobj, const struct attribute_group *attr, const char* name) 
{
	int status = sysfs_create_group(kobj, attr);  
        if(status) { 
                pddf_dbg(LED, KERN_ERR "Driver ERROR: sysfs_create %s failed rc=%d\n", name, status); 
	}
}


static int __init led_init(void) {
	struct kobject *device_kobj;
	pddf_dbg(LED, KERN_INFO "PDDF GENERIC LED MODULE init..\n");

        device_kobj = get_device_i2c_kobj();
        if(!device_kobj) 
                return -ENOMEM;

	KBOJ_CREATE("platform", device_kobj, &platform_kobj);
	KBOJ_CREATE("led", device_kobj, &led_kobj);
	KBOJ_CREATE("on", led_kobj, &on_kobj);
	KBOJ_CREATE("off", led_kobj, &off_kobj);
	KBOJ_CREATE("blink", led_kobj, &blink_kobj);
	KBOJ_CREATE("faulty", led_kobj, &faulty_kobj);
	KBOJ_CREATE("cur_state", led_kobj, &cur_state_kobj);

        LED_DEV_ATTR_CREATE(platform_kobj, &attr_group_platform, "attr_group_platform");
        LED_DEV_ATTR_CREATE(led_kobj, &attr_group_dev, "attr_group_dev");
        LED_DEV_ATTR_CREATE(on_kobj, &attr_group_on, "attr_group_on");
        LED_DEV_ATTR_CREATE(off_kobj, &attr_group_off, "attr_group_off");
        LED_DEV_ATTR_CREATE(faulty_kobj, &attr_group_faulty, "attr_group_faulty");
        LED_DEV_ATTR_CREATE(blink_kobj, &attr_group_blink, "attr_group_blink");
        LED_DEV_ATTR_CREATE(cur_state_kobj, &attr_group_cur_state, "attr_group_cur_state");
	return (0);
}


static void __exit led_exit(void) {
	pddf_dbg(LED, "PDDF GENERIC LED MODULE exit..\n");
	free_kobjs();
	if(psu_led_ops_data) kfree(psu_led_ops_data);
	if(fantray_led_ops_data) kfree(fantray_led_ops_data);
}

module_init(led_init);
module_exit(led_exit);

MODULE_AUTHOR("Broadcom");
MODULE_DESCRIPTION("led driver");
MODULE_LICENSE("GPL");
