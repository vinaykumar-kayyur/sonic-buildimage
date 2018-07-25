<<<<<<< HEAD
BRCM_SAI = libsaibcm_3.1.3.4-13_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_3.1.3.4-13_amd64.deb?sv=2015-04-05&sr=b&sig=Y7mQMOnQEzwb%2FG%2BY9dcEX0Y9tQBDCK2UmF4TjIz3Zn8%3D&se=2155-04-24T09%3A52%3A42Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.1.3.4-13_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_3.1.3.4-13_amd64.deb?sv=2015-04-05&sr=b&sig=YYjwAt47PlCYJgW0RtEsdcmGAc52UdAzHEd5qVKImxc%3D&se=2155-04-24T09%3A53%3A45Z&sp=r"
=======
BRCM_SAI = libsaibcm_3.1.3.4-15_amd64.deb
$(BRCM_SAI)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm_3.1.3.4-15_amd64.deb?sv=2015-04-05&sr=b&sig=7CIkdlBB%2BY6Xjae0vc1QBnlAVedRkreJRhWM93SyHOI%3D&se=2032-02-29T18%3A31%3A54Z&sp=r"

BRCM_SAI_DEV = libsaibcm-dev_3.1.3.4-15_amd64.deb
$(eval $(call add_derived_package,$(BRCM_SAI),$(BRCM_SAI_DEV)))
$(BRCM_SAI_DEV)_URL = "https://sonicstorage.blob.core.windows.net/packages/libsaibcm-dev_3.1.3.4-15_amd64.deb?sv=2015-04-05&sr=b&sig=rBOT802o1o%2BAcogaXq%2FgqyuTAmSlFKhtPzYM%2BtXlIdM%3D&se=2032-02-29T18%3A34%3A10Z&sp=r"
>>>>>>> 14a0de768d532fa55bc58d3df7075786d2ae1876

SONIC_ONLINE_DEBS += $(BRCM_SAI) $(BRCM_SAI_DEV)
$(BRCM_SAI_DEV)_DEPENDS += $(BRCM_SAI)
