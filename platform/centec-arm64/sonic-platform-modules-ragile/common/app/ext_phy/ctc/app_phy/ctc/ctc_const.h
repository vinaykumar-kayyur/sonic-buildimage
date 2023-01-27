/**
 @file ctc_const.h

 @date 2009-10-27

 @version v2.0

The file define  all CTC SDK module's  common Macros and constant.
*/

#ifndef _CTC_CONST_H
#define _CTC_CONST_H
#ifdef __cplusplus
extern "C" {
#endif
/****************************************************************
 *
 * Header Files
 *
 ***************************************************************/

/****************************************************************
*
* Defines and Macros
*
****************************************************************/
/**
 @defgroup const    CONST
 @{
*/

#define CTC_UINT32_BITS                 32
#define CTC_UINT8_BITS                  8

#define CTC_MAX_UINT16_VALUE            0xFFFF      /**< Max unsigned 16bit value */
#define CTC_MAX_UINT32_VALUE            0xFFFFFFFF  /**< Max unsigned 32bit value */
#define CTC_MAX_UINT8_VALUE             0xFF        /**< Max unsigned 8bit value */

#define CTC_MAX_CHIP_NUM                32

/**@} end of @desfgroup  const CONST */

#ifdef __cplusplus
}
#endif

#endif /* _CTC_CONST_H*/
