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
	{ 0xce9a3be4, __VMLINUX_SYMBOL_STR(platform_driver_unregister) },
	{ 0xed7b07d1, __VMLINUX_SYMBOL_STR(platform_device_unregister) },
	{ 0x967d0d79, __VMLINUX_SYMBOL_STR(platform_device_register) },
	{ 0x814296af, __VMLINUX_SYMBOL_STR(__platform_driver_register) },
	{ 0x60ea2d6, __VMLINUX_SYMBOL_STR(kstrtoull) },
	{ 0x91715312, __VMLINUX_SYMBOL_STR(sprintf) },
	{ 0x6d0aba34, __VMLINUX_SYMBOL_STR(wait_for_completion) },
	{ 0x78fd36e7, __VMLINUX_SYMBOL_STR(ipmi_request_supply_msgs) },
	{ 0xf432dd3d, __VMLINUX_SYMBOL_STR(__init_waitqueue_head) },
	{ 0x423b776a, __VMLINUX_SYMBOL_STR(ipmi_create_user) },
	{ 0xbc0cc073, __VMLINUX_SYMBOL_STR(i2c_add_mux_adapter) },
	{ 0xd2b09ce5, __VMLINUX_SYMBOL_STR(__kmalloc) },
	{ 0x40defe54, __VMLINUX_SYMBOL_STR(sysfs_create_group) },
	{ 0x675f140a, __VMLINUX_SYMBOL_STR(i2c_new_dummy) },
	{ 0x27e1a049, __VMLINUX_SYMBOL_STR(printk) },
	{ 0xbe4537c9, __VMLINUX_SYMBOL_STR(sysfs_remove_group) },
	{ 0x37a0cba, __VMLINUX_SYMBOL_STR(kfree) },
	{ 0xaf6a7823, __VMLINUX_SYMBOL_STR(i2c_del_mux_adapter) },
	{ 0xed4d1c86, __VMLINUX_SYMBOL_STR(i2c_put_adapter) },
	{ 0xd1fea71f, __VMLINUX_SYMBOL_STR(i2c_unregister_device) },
	{ 0xd92aa4eb, __VMLINUX_SYMBOL_STR(i2c_new_device) },
	{ 0x62a9a216, __VMLINUX_SYMBOL_STR(i2c_get_adapter) },
	{ 0x3a401b73, __VMLINUX_SYMBOL_STR(dev_err) },
	{ 0xfcb77cfd, __VMLINUX_SYMBOL_STR(ipmi_free_recv_msg) },
	{ 0x4b06d2e7, __VMLINUX_SYMBOL_STR(complete) },
	{ 0xbdfb6dbb, __VMLINUX_SYMBOL_STR(__fentry__) },
};

static const char __module_depends[]
__used
__attribute__((section(".modinfo"))) =
"depends=ipmi_msghandler,i2c-mux,i2c-core";

