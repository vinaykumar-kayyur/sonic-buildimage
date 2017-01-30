BRCM_OPENNSL = libopennsl_3.2.1.5-5-20170130215804.17_amd64.deb
$(BRCM_OPENNSL)_URL = "https://sonicstorage.blob.core.windows.net/packages/libopennsl_3.2.1.5-5-20170130215804.17_amd64.deb?sv=2015-04-05&sr=b&sig=3L7NY8WiSpBIhJzxUgn4XkqP7YHoQdBVY2XPtQl6bC8%3D&se=2030-10-09T23%3A08%3A08Z&sp=r"

BRCM_OPENNSL_KERNEL = opennsl-modules-3.16.0-4-amd64_3.2.1.5-5-20170130215804.17_amd64.deb
$(BRCM_OPENNSL_KERNEL)_URL = "https://sonicstorage.blob.core.windows.net/packages/opennsl-modules-3.16.0-4-amd64_3.2.1.5-5-20170130215804.17_amd64.deb?sv=2015-04-05&sr=b&sig=f2eXwLzdyRqijB1NvqxhSgtND3YI0cZAVxDBXWdhEQ8%3D&se=2030-10-09T23%3A08%3A42Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_OPENNSL) $(BRCM_OPENNSL_KERNEL)
