# Changing the virtual device

You can control the hw sku and default factory configuration for the VS image 
by modifying the content of the file default_sku. 

The format of default_sku is a single line:

```
<hw_key> <default_preset>
```

## Allowable values for hw_key

| hw_key | Device |
| ------ | ------ |
| Force10-S6000 | Dell Force10 S6000|
| brcm_gearbox_vs | Similar to Force10-S6000, but implements a virtual BRCM81724 Gearbox Phy |

## Allowable values for default_preset

These include "t1", "l2", and "empty". See the file 
sonic-buildimage/src/sonic-config-engine/config_samples.py for details on how 
each default_preset value is interpreted.

