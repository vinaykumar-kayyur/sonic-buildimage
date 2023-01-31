#include <linux/kernel.h> /* Wd're doing kernel work */  
#include <linux/module.h> /* specifically, a module */  
#include <linux/init.h>   /* Need for the macros */
#include <linux/moduleparam.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include "ragile.h"

/* static int32_t addr = 0x000300AB; */
/* module_param(addr, long, S_IRUGO); */

static long witrevalue = 0x54;
module_param(witrevalue, long, S_IRUGO);

static int readwrite = 0;
module_param(readwrite, int, S_IRUGO);

static int debug = 0;
module_param(debug, int, S_IRUGO);

static void testRead(void) 
{
    struct file *file = NULL;
    mm_segment_t old_fs;
    char buf[128];

    memset(buf, 0, 128);
    file = filp_open("/test.txt", O_RDWR | O_APPEND | O_CREAT, 0644);
    if (IS_ERR(file)) {
            pr_err("error open file\n");
            return ;
    }
    
    old_fs = get_fs();
    set_fs(KERNEL_DS);
    vfs_read(file, buf, 128, &file->f_pos);
    pr_err("%s", buf);
    set_fs(old_fs);
    filp_close(file, NULL);

    return (void)0;
    

}


static int __init test_init(void)
{    
    ragile_setdebug(debug);
    testRead(); 

    return 0;
}

static void __exit test_exit(void)
{
    pr_err("finish test_exit ko\n");
    ragile_setdebug(0);
}

module_init(test_init);
module_exit(test_exit);


MODULE_AUTHOR("test <test@test>");
MODULE_DESCRIPTION("test");
MODULE_LICENSE("GPL");

