# Prepare

Before you use Centec PHY Driver, you need implement your own MDIO interface in driver/src/phy_drv_interface.c.
```
#ifdef APP_PHY

/**
*@fn int32 ctc_phy_mdio_read(uint8 lchip_id, ctc_chip_mdio_type_t type, ctc_chip_mdio_para_t* p_para)
*@brief ctc_phy_mdio_read for mdio read
*@param[in] lchip_id asic chip id
*@param[in] type mdio bus type
*@param[in,out] p_para point to mdio access parameter
*/
int32
ctc_phy_mdio_read(uint8 lchip_id, ctc_chip_mdio_type_t type, ctc_chip_mdio_para_t* p_para)
{
    /* add you code for mdio access */
    return 0;
}

/**
*@fn int32 ctc_phy_mdio_write(uint8 lchip_id, ctc_chip_mdio_type_t type, ctc_chip_mdio_para_t* p_para)
*@brief ctc_phy_mdio_write for mdio write
*@param[in] lchip_id asic chip id
*@param[in] type mdio bus type
*@param[in,out] p_para point to mdio access parameter
*/
int32
ctc_phy_mdio_write(uint8 lchip_id, ctc_chip_mdio_type_t type, ctc_chip_mdio_para_t* p_para)
{
    /* add you code for mdio access */
    return 0;
}

#endif

```
# Application

According to the Centec_PHY_Driver_Application_note.pdf, you can implement your own application with Centec PHY Driver.


