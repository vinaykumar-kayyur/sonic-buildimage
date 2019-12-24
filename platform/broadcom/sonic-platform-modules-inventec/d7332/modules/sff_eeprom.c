/*
 sff_eeprom.c
 provide api for accesing sff eeprom
 
 */
#include <linux/kobject.h>
#include <linux/string.h>
#include <linux/sysfs.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/device.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/slab.h>
#include <linux/i2c.h>
#include <linux/mutex.h>
#include <linux/delay.h>
#include "sff_eeprom.h"
#include "inv_def.h"
#include "sff_io.h"
#include "sff.h"
#include "eeprom_config/eeprom_config.h"

/*
 * This module implement sff platform driver and provide sysfs attribute for access io control
 * and eeprom 
 * 
 */
#define DEBUG_MODE (0)

#if (DEBUG_MODE == 1)
#define SFF_PLATFORM_DEBUG(fmt, args...) \
printk (KERN_INFO "%s: " fmt "\r\n", __FUNCTION__,  ##args)
#else
#define SFF_PLATFORM_DEBUG(fmt, args...)
#endif

#if (DEBUG_MODE == 1)
#define SFF_PLATFORM_INFO(fmt, args...) printk( KERN_INFO "[SFF_PLATFORM] " fmt, ##args)
#else
    #define SFF_PLATFORM_INFO(fmt, args...)
#endif

#define SFF_PLATFORM_ERR(fmt, args...) printk( KERN_ERR "[SFF_PLATFORM] " fmt, ##args)

struct sff_eeprom_t
{
    int port;
    struct i2c_client *i2c_client;
    struct mutex lock;
};
struct eeprom_i2c_tbl_t *Eeprom_I2c_Tbl = NULL;
struct sff_eeprom_t *Sff_Eeprom = NULL;
int sff_eeprom_read(int port,
                            u8 slave_addr,
                            u8 offset,
                            u8 *buf,
                            size_t len);

int sff_eeprom_write(int port,
                                    u8 slave_addr,
                                    u8 offset,
                                    const u8 *buf,
                                    size_t len);


static int _sff_eeprom_read(struct sff_eeprom_t *eeprom, 
                                  u8 slave_addr, 
                                  u8 offset, 
                                  u8 *buf, 
                                  size_t len)
{
    struct i2c_client *client = NULL;
    struct mutex *lock = NULL;
    int ret = 0;
    int count = 0;
    u8 *ptr = buf;
    
    if(IS_ERR_OR_NULL(eeprom))
      return -1;
    
    lock = &(eeprom->lock);
    client = eeprom->i2c_client;
    
    if(IS_ERR_OR_NULL(ptr) || 
       IS_ERR_OR_NULL(client))
       return -1;
    
    mutex_lock(lock);
    client->addr = slave_addr;
    for(count = 0; count < len; count++)
    {    
        ret = i2c_smbus_read_byte_data(client, offset+count);
        if (ret < 0)
        {
            SFF_PLATFORM_INFO("i2c_read fail ret:%d\n", ret);
            mutex_unlock(lock);

            return ret;
        }
        ptr[count] = (u8)ret;
    }
    
    mutex_unlock(lock);
#ifdef READBACK_CHECK
    for(count = 0; count < len; count++)
    {    
        SFF_PLATFORM_DEBUG("i2c_read ok buf[%d]:0x%x\n", count, buf[count]);
    }
#endif    
    return 0;    

}    

static int _sff_eeprom_write(struct sff_eeprom_t *eeprom, 
                                   u8 slave_addr, 
                                   u8 offset, 
                                   const u8 *buf, 
                                   size_t len)
{

    struct i2c_client *client = NULL;
    struct mutex *lock = NULL;
    int ret = 0;
    int count = 0;
    const u8 *ptr = buf;
    
    if(IS_ERR_OR_NULL(eeprom))
      return -1;

    lock = &(eeprom->lock);
    client = eeprom->i2c_client;
    
    if(IS_ERR_OR_NULL(ptr) || 
       IS_ERR_OR_NULL(client))
       return -1;
    
    mutex_lock(lock);
    client->addr = slave_addr;
    for(count = 0; count < len; count++)
    {    
        ret = i2c_smbus_write_byte_data(client, offset+count, ptr[count]);
        if (ret < 0)
        {
            SFF_PLATFORM_INFO("i2c_read fail ret:%d\n", ret);
            mutex_unlock(lock);
            return -1;
        }
    }

    mutex_unlock(lock);
    return 0;    

}
int sff_eeprom_read(int port, 
                            u8 slave_addr, 
                            u8 offset, 
                            u8 *buf, 
                            size_t len)
{
    
    return _sff_eeprom_read(&Sff_Eeprom[port], slave_addr, offset, buf, len);
    
}
EXPORT_SYMBOL(sff_eeprom_read);

int sff_eeprom_write(int port, 
                     u8 slave_addr, 
                     u8 offset, 
                     const u8 *buf, 
                     size_t len)
{
    return _sff_eeprom_write(&Sff_Eeprom[port], slave_addr, offset, buf, len);
}
EXPORT_SYMBOL(sff_eeprom_write);

#if 0
static int _sff_eeprom_obj_init(struct sff_eeprom_t *eeprom,  struct eeprom_config_t *config)
{
    struct i2c_client *client = NULL;
    struct i2c_adapter *adap;
    int use_smbus = 0;
    
    if (IS_ERR_OR_NULL(eeprom) ||
        IS_ERR_OR_NULL(config)) {
        goto exit_err;
    }    

    client = kzalloc(sizeof(struct i2c_client), GFP_KERNEL);  
    
    if (IS_ERR_OR_NULL(client)) {
        goto exit_err;
    }    
    
    //get i2c adapter    
    eeprom->port = config->port;
    adap = i2c_get_adapter(config->i2c_ch);
    client->adapter = adap;
    client->addr = 0x50;
    if (!i2c_check_functionality(client->adapter,
        I2C_FUNC_SMBUS_BYTE_DATA | I2C_FUNC_SMBUS_WORD_DATA))
    {    
        SFF_PLATFORM_ERR("%s: i2c check fail\n", __FUNCTION__);
        goto exit_kfree_sff_client;

    }
    else
    {
        if(i2c_check_functionality(client->adapter,I2C_FUNC_SMBUS_BYTE_DATA))
           use_smbus = I2C_FUNC_SMBUS_BYTE_DATA;
        else
           use_smbus = I2C_FUNC_SMBUS_WORD_DATA;      
         
    }    

    eeprom->i2c_client = client;
    SFF_PLATFORM_INFO("%s: i2c check ok ya: use_smbus:0x%x port:%d\n", __FUNCTION__, 
                     use_smbus, eeprom->port);
    mutex_init(&(eeprom->lock));
    return 0;
    
    exit_kfree_sff_client:
    i2c_put_adapter(client->adapter);
    kfree(client);
    exit_err:

    return -1;
}   
#endif
static int sff_eeprom_client_create(int size)
{

    struct i2c_client *client = NULL;
    int port_num = 0;
    int port = 0;
    port_num = size;
    
    for (port = 0; port < port_num; port++) {

        client = kzalloc(sizeof(struct i2c_client), GFP_KERNEL);  
        
        if (IS_ERR_OR_NULL(client)) {
            return -ENOMEM;
        }    
        
        Sff_Eeprom[port].i2c_client = client;
    }
        
    return 0;
}    
static int _sff_eeprom_obj_init(struct sff_eeprom_t *eeprom,  struct eeprom_config_t *config)
{
    struct i2c_adapter *adap;
    struct i2c_client *client = NULL;
    
    if (IS_ERR_OR_NULL(eeprom) ||
        IS_ERR_OR_NULL(config)) {
        return -EBADRQC;
    }    
    client = eeprom->i2c_client; 
    adap = i2c_get_adapter(config->i2c_ch);
    client->adapter = adap;
    client->addr = 0x50;
    
    if (!i2c_check_functionality(client->adapter,
        I2C_FUNC_SMBUS_BYTE_DATA | I2C_FUNC_SMBUS_WORD_DATA))
    {    
        SFF_PLATFORM_ERR("%s: i2c check fail\n", __FUNCTION__);
        return -EBADRQC;

    }

    eeprom->i2c_client = client;
    SFF_PLATFORM_INFO("%s: i2c check ok ya: use_smbus:0x%x port:%d\n", __FUNCTION__, 
                     use_smbus, eeprom->port);
    mutex_init(&(eeprom->lock));
    return 0;
    
}   
static void sff_eeprom_obj_deinit(int size)
{
    int port = 0;
    int port_num = size;
    struct i2c_client *client = NULL;
     
    if (!Sff_Eeprom) {

        SFF_PLATFORM_ERR("NULL pointer\n");
        return;
    }
    for (port = 0; port < port_num; port++)
    {
        client = Sff_Eeprom[port].i2c_client;
        if (!client) {

            SFF_PLATFORM_ERR("NULL pointer\n");
            return;
        }   

        i2c_put_adapter(client->adapter);
    }
}

static void sff_eeprom_client_destroy(int size)
{

    int port = 0;
    int port_num = size;
    struct i2c_client *client = NULL;
    
    for (port = 0; port < port_num; port++)
    {
        client = Sff_Eeprom[port].i2c_client;
        if (!IS_ERR_OR_NULL(client)) {
            kfree(client);
        }
    }
}    

static int sff_eeprom_obj_init(struct eeprom_i2c_tbl_t *tbl)
{
    int port = 0;
    int port_num = 0;
    struct eeprom_config_t *map = NULL;
  
    if(IS_ERR_OR_NULL(tbl)) {
        return -EBADRQC;
    }
    port_num = tbl->size;
    map = tbl->map; 
    for (port = 0; port < port_num; port++)
    {    

        if (_sff_eeprom_obj_init(&Sff_Eeprom[port], &map[port]) < 0)
        {
            return -EBADRQC;
        }    
    }
    
    return 0;


}    
static int sff_eeprom_obj_create(int size)
{
            
    Sff_Eeprom = kzalloc(sizeof(struct sff_eeprom_t) * size, GFP_KERNEL);
        
    if(IS_ERR_OR_NULL(Sff_Eeprom))
    {
        return -ENOMEM;
    }    
    
    return 0;
}   

static struct eeprom_i2c_tbl_t *_platform_eeprom_info_load(int platform_name)
{
    int i = 0;
    struct eeprom_i2c_tbl_t *tbl = NULL;
    for (i = 0; platform_eeprom_info_tbl[i].platform_name != PLATFORM_END; i++) {
        if (platform_eeprom_info_tbl[i].platform_name == platform_name) {

            tbl = platform_eeprom_info_tbl[i].tbl;
            return tbl;
        }
    } 

    return NULL;
}    

static int eeprom_i2c_table_load(void)
{
    int platform_name = PLATFORM_NAME;
    struct eeprom_i2c_tbl_t *tbl = NULL;
    tbl = _platform_eeprom_info_load(platform_name);
    if (!tbl) {

        return -1;
    }
    Eeprom_I2c_Tbl = tbl;
    return 0;
}    
static void sff_eeprom_obj_destroy(void)
{
    if(!IS_ERR_OR_NULL(Sff_Eeprom)) {
        kfree(Sff_Eeprom);    
    }
}
static int _sff_eeprom_init(void)
{
    SFF_PLATFORM_INFO("%s\n", __FUNCTION__);
    if (eeprom_i2c_table_load() < 0)
    {
        goto exit_err;
    }    
    if (sff_eeprom_obj_create(Eeprom_I2c_Tbl->size) < 0)
    {
        goto exit_err;
    }
    
    if (sff_eeprom_client_create(Eeprom_I2c_Tbl->size) < 0)
    {
        goto exit_kfree_eeprom_obj;
    }

    if (sff_eeprom_obj_init(Eeprom_I2c_Tbl) < 0)
    {

        goto exit_kfree_eeprom_client;
    }    

    SFF_PLATFORM_INFO("%s ok\n", __FUNCTION__);
    return 0;

    exit_kfree_eeprom_client:
    sff_eeprom_client_destroy(Eeprom_I2c_Tbl->size);
    exit_kfree_eeprom_obj:
    sff_eeprom_obj_destroy();

    exit_err:
    return -1;
}    


int sff_eeprom_init(void)
{
	int retval = 0;
    retval = _sff_eeprom_init();    
    return retval;
}
EXPORT_SYMBOL(sff_eeprom_init);

void sff_eeprom_deinit(void)
{
    sff_eeprom_obj_deinit(Eeprom_I2c_Tbl->size);
    sff_eeprom_client_destroy(Eeprom_I2c_Tbl->size);
    sff_eeprom_obj_destroy();

    SFF_PLATFORM_INFO("%s ok\n", __FUNCTION__);
}
EXPORT_SYMBOL(sff_eeprom_deinit);

#if 0
static int __init example_init(void)
{
	int retval = 0;
    retval = sff_platform_init();    
    return retval;

}
static void __exit example_exit(void)
{
    sff_eeprom_obj_destroy();
    sff_driver_unregister();
}


module_init(example_init);
module_exit(example_exit);
#endif
MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("alang");
