BRCM_SAI = libsaibcm_3.1.3.5-4_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/libsaibcm_3.1.3.5-4_amd64.deb?sv=2015-04-05&sr=b&sig=eGzYPd5iKbNq3m9xcb6WKJV54y57UZcgjkcGoJl7ugM%3D&se=2155-06-07T03%3A56%3A28Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.1.3.5-4_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmsai/libsaibcm-dev_3.1.3.5-4_amd64.deb?sv=2015-04-05&sr=b&sig=QPeaOT%2BmJsXNWSAf7%2BcdpHQR7m1MQn%2BtPp5S6qo9XRw%3D&se=2155-06-07T03%3A55%3A44Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_SAI) $(BRCM_SAI_DEV)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
