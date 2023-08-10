/**
 @file phy_interface.c
 @copyright Copyright(C)  Centec Networks Inc.  All rights reserved.
 @date 2019-10-23
 @version v1.0
*/
#include <dlfcn.h>
#include "sal.h"
#include "phy_drv_def.h"
#include "phy_drv_common.h"
#include "phy_drv_api.h"

#define CTCSDK_LIB_DL_PATH          "/usr/lib/libctcsdk.so"
#define CTCSDK_MDIO_WRITE_SYMBOL    "ctcs_chip_mdio_write"
#define CTCSDK_MDIO_READ_SYMBOL     "ctcs_chip_mdio_read"

#ifdef SDK_PHY
extern uint8 g_api_lchip;
extern uint8 g_ctcs_api_en;
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
    if (g_ctcs_api_en)
    {
        return ctcs_chip_mdio_read(g_api_lchip, type, p_para);
    }
    else
    {
        return ctc_chip_mdio_read(lchip_id, type, p_para);
    }
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
    if (g_ctcs_api_en)
    {
        return ctcs_chip_mdio_write(g_api_lchip, type, p_para);
    }
    else
    {
        return ctc_chip_mdio_write(lchip_id, type, p_para);
    }
}
#endif

cust_ctc_mdio_write_f cust_ctc_mdio_write;
cust_ctc_mdio_read_f cust_ctc_mdio_read;

#ifdef APP_PHY

int32 ctc_phy_mdio_init(void)
{
    void* ctcsdk_dl_hdl;

    if (!cust_ctc_mdio_write || !cust_ctc_mdio_read) {
        ctcsdk_dl_hdl = dlopen(CTCSDK_LIB_DL_PATH, RTLD_LAZY);
        if (!ctcsdk_dl_hdl) {
            PHY_LOG_ERR("%s\n", dlerror());
            return CTC_E_NOT_EXIST;
        }
        cust_ctc_mdio_write = (cust_ctc_mdio_write_f)dlsym(ctcsdk_dl_hdl, CTCSDK_MDIO_WRITE_SYMBOL);
        if (!cust_ctc_mdio_write) {
            PHY_LOG_ERR("%s\n", dlerror());
            dlclose(ctcsdk_dl_hdl);
            return CTC_E_NOT_EXIST;
        }

        cust_ctc_mdio_read = (cust_ctc_mdio_read_f)dlsym(ctcsdk_dl_hdl, CTCSDK_MDIO_READ_SYMBOL);
        if (!cust_ctc_mdio_read) {
            PHY_LOG_ERR("%s\n", dlerror());
            dlclose(ctcsdk_dl_hdl);
            return CTC_E_NOT_EXIST;
        }

    }

    return CTC_E_NONE;
}

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
    int32 rv;

    if (!cust_ctc_mdio_read) {
        PHY_LOG_ERR("cust_ctc_mdio_read is null\n");
        return CTC_E_NOT_EXIST;
    }

    rv =  cust_ctc_mdio_read(lchip_id, type, p_para);
    if (rv) {
        PHY_LOG_ERR("cust_ctc_mdio_read fail, bus:%d addr:%d reg:%d rv:%d\n",
            p_para->bus, p_para->phy_addr, p_para->reg, rv);
    }

    return rv;
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
    int32 rv;

    if (!cust_ctc_mdio_write) {
        PHY_LOG_ERR("cust_ctc_mdio_write is null\n");
        return CTC_E_NOT_EXIST;
    }

    rv = cust_ctc_mdio_write(lchip_id, type, p_para);
    if (rv) {
        PHY_LOG_ERR("cust_ctc_mdio_write fail, bus:%d addr:%d reg:%d val:%d rv:%d\n",
            p_para->bus, p_para->phy_addr, p_para->reg, p_para->value, rv);
    }

    return rv;
}

#endif
