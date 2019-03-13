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
	{ 0xafd29968, __VMLINUX_SYMBOL_STR(kmalloc_caches) },
	{ 0x4260eed4, __VMLINUX_SYMBOL_STR(i2c_smbus_read_byte_data) },
	{ 0x1b17e06c, __VMLINUX_SYMBOL_STR(kstrtoll) },
	{ 0x9c570ac1, __VMLINUX_SYMBOL_STR(i2c_del_driver) },
	{ 0x203a5877, __VMLINUX_SYMBOL_STR(i2c_smbus_write_byte_data) },
	{ 0x2ae2afc6, __VMLINUX_SYMBOL_STR(mutex_unlock) },
	{ 0x91715312, __VMLINUX_SYMBOL_STR(sprintf) },
	{ 0xb176390a, __VMLINUX_SYMBOL_STR(sysfs_remove_group) },
	{ 0x343a1a8, __VMLINUX_SYMBOL_STR(__list_add) },
	{ 0xb3434297, __VMLINUX_SYMBOL_STR(__mutex_init) },
	{ 0x3a00106f, __VMLINUX_SYMBOL_STR(sysfs_create_group) },
	{ 0x5b660ab0, __VMLINUX_SYMBOL_STR(mutex_lock) },
	{ 0x521445b, __VMLINUX_SYMBOL_STR(list_del) },
	{ 0xd777586b, __VMLINUX_SYMBOL_STR(i2c_register_driver) },
	{ 0xa8bdb2b7, __VMLINUX_SYMBOL_STR(_dev_info) },
	{ 0xdb7305a1, __VMLINUX_SYMBOL_STR(__stack_chk_fail) },
	{ 0x2ea2c95c, __VMLINUX_SYMBOL_STR(__x86_indirect_thunk_rax) },
	{ 0xbdfb6dbb, __VMLINUX_SYMBOL_STR(__fentry__) },
	{ 0x1430a3de, __VMLINUX_SYMBOL_STR(kmem_cache_alloc_trace) },
	{ 0x301ef78d, __VMLINUX_SYMBOL_STR(__dynamic_dev_dbg) },
	{ 0x37a0cba, __VMLINUX_SYMBOL_STR(kfree) },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=";

MODULE_ALIAS("i2c:fn_6254_dn_f_cpld");
