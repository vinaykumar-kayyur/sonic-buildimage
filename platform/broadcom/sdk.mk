BRCM_OPENNSL = libopennsl_3.2.1.5_amd64.deb
$(BRCM_OPENNSL)_URL = "https://sonicstorage.blob.core.windows.net/packages/libopennsl_3.2.1.5_amd64.deb?sv=2015-04-05&sr=b&sig=qm6%2BkiGuRGsFKwZcUz6yEtbgbbwQuhxEr0chLM7qJEQ%3D&se=2030-09-02T21%3A41%3A11Z&sp=r"

BRCM_OPENNSL_KERNEL = opennsl-modules-3.16.0-4-amd64_3.2.1.5_amd64.deb
$(BRCM_OPENNSL_KERNEL)_URL = "https://sonicstorage.blob.core.windows.net/packages/opennsl-modules-3.16.0-4-amd64_3.2.1.5_amd64.deb?sv=2015-04-05&sr=b&sig=c8hO5PQpvod7IX3aYOiyvFB9rICxDgGiFF5g3GDHx84%3D&se=2030-09-02T21%3A42%3A34Z&sp=r"

BCMCMD = bcmcmd
$(BCMCMD)_URL = "https://sonicstorage.blob.core.windows.net/packages/bcmcmd?sv=2015-04-05&sr=b&sig=X3bFApmsNFmcnWM9mSGRxBugPcg%2FgJCHh5hhSuV1M2c%3D&se=2030-08-23T14%3A41%3A56Z&sp=r"

DSSERVE = dsserve
$(DSSERVE)_URL = "https://sonicstorage.blob.core.windows.net/packages/dsserve?sv=2015-04-05&sr=b&sig=aMlnRA%2FXZNmHPgmOj%2FNMJMYLWyvva1QrN4HcsVXvqKA%3D&se=2030-08-23T14%3A42%3A32Z&sp=r"

SONIC_ONLINE_DEBS += $(BRCM_OPENNSL) $(BRCM_OPENNSL_KERNEL)
SONIC_ONLINE_FILES += $(BCMCMD) $(DSSERVE)
