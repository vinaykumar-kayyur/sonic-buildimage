#include <linux/module.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

MODULE_INFO(vermagic, VERMAGIC_STRING);

__visible struct module __this_module
__attribute__((section(".gnu.linkonce.this_module"))) = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif

static const struct modversion_info ____versions[]
__used
__attribute__((section("__versions"))) = {
	{ 0xe15704bf, __VMLINUX_SYMBOL_STR(module_layout) },
	{ 0x1ac909da, __VMLINUX_SYMBOL_STR(param_ops_uint) },
	{ 0x9c570ac1, __VMLINUX_SYMBOL_STR(i2c_del_driver) },
	{ 0xd777586b, __VMLINUX_SYMBOL_STR(i2c_register_driver) },
	{ 0x91715312, __VMLINUX_SYMBOL_STR(sprintf) },
	{ 0x27e1a049, __VMLINUX_SYMBOL_STR(printk) },
	{ 0x37a0cba, __VMLINUX_SYMBOL_STR(kfree) },
	{ 0x3a00106f, __VMLINUX_SYMBOL_STR(sysfs_create_group) },
	{ 0xb3434297, __VMLINUX_SYMBOL_STR(__mutex_init) },
	{ 0x1430a3de, __VMLINUX_SYMBOL_STR(kmem_cache_alloc_trace) },
	{ 0xafd29968, __VMLINUX_SYMBOL_STR(kmalloc_caches) },
	{ 0xdb7305a1, __VMLINUX_SYMBOL_STR(__stack_chk_fail) },
	{ 0xc32c1083, __VMLINUX_SYMBOL_STR(pegatron_fn_6254_dn_f_cpld_read) },
	{ 0x450ee588, __VMLINUX_SYMBOL_STR(i2c_smbus_read_i2c_block_data) },
	{ 0x4260eed4, __VMLINUX_SYMBOL_STR(i2c_smbus_read_byte_data) },
	{ 0x2ae2afc6, __VMLINUX_SYMBOL_STR(mutex_unlock) },
	{ 0xccb87818, __VMLINUX_SYMBOL_STR(i2c_smbus_read_word_data) },
	{ 0xf9a482f9, __VMLINUX_SYMBOL_STR(msleep) },
	{ 0xaadcf1c1, __VMLINUX_SYMBOL_STR(i2c_transfer) },
	{ 0x15ba50a6, __VMLINUX_SYMBOL_STR(jiffies) },
	{ 0x7f02188f, __VMLINUX_SYMBOL_STR(__msecs_to_jiffies) },
	{ 0x5b660ab0, __VMLINUX_SYMBOL_STR(mutex_lock) },
	{ 0xd3bd94fe, __VMLINUX_SYMBOL_STR(pegatron_fn_6254_dn_f_cpld_write) },
	{ 0xe2d5255a, __VMLINUX_SYMBOL_STR(strcmp) },
	{ 0x301ef78d, __VMLINUX_SYMBOL_STR(__dynamic_dev_dbg) },
	{ 0xb176390a, __VMLINUX_SYMBOL_STR(sysfs_remove_group) },
	{ 0xbdfb6dbb, __VMLINUX_SYMBOL_STR(__fentry__) },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=pegatron_fn_6254_dn_f_cpld";

MODULE_ALIAS("i2c:fn_6254_dn_f_sfpA");
MODULE_ALIAS("i2c:fn_6254_dn_f_sfpB");
MODULE_ALIAS("i2c:fn_6254_dn_f_sfpC");
