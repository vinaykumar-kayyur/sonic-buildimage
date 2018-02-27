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

static const struct modversion_info ____versions[]
__used
__attribute__((section("__versions"))) = {
	{ 0x533a1566, __VMLINUX_SYMBOL_STR(module_layout) },
	{ 0x8733c9e1, __VMLINUX_SYMBOL_STR(kmalloc_caches) },
	{ 0xeae3dfd6, __VMLINUX_SYMBOL_STR(__const_udelay) },
	{ 0x1b3a55f5, __VMLINUX_SYMBOL_STR(i2c_add_adapter) },
	{ 0x3a401b73, __VMLINUX_SYMBOL_STR(dev_err) },
	{ 0x27e1a049, __VMLINUX_SYMBOL_STR(printk) },
	{ 0xfd3f559f, __VMLINUX_SYMBOL_STR(i2c_del_adapter) },
	{ 0x42c8de35, __VMLINUX_SYMBOL_STR(ioremap_nocache) },
	{ 0xbdfb6dbb, __VMLINUX_SYMBOL_STR(__fentry__) },
	{ 0xab905eb7, __VMLINUX_SYMBOL_STR(pci_unregister_driver) },
	{ 0x20705009, __VMLINUX_SYMBOL_STR(kmem_cache_alloc_trace) },
	{ 0xec9512d1, __VMLINUX_SYMBOL_STR(pci_bus_write_config_byte) },
	{ 0x37a0cba, __VMLINUX_SYMBOL_STR(kfree) },
	{ 0xedc03953, __VMLINUX_SYMBOL_STR(iounmap) },
	{ 0xe729a53d, __VMLINUX_SYMBOL_STR(__pci_register_driver) },
	{ 0x47c8baf4, __VMLINUX_SYMBOL_STR(param_ops_uint) },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=i2c-core";

MODULE_ALIAS("pci:v00008086d00008C3Asv*sd*bc*sc*i*");
