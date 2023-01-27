/****************************************************************************
 *file ctc_macro.h

 *author  Copyright (C) 2011 Centec Networks Inc.  All rights reserved.

 *date 2009-11-26

 *version v2.0

The file define  all CTC SDK module's  common Macros
 ****************************************************************************/

#ifndef _CTC_MACRO_H
#define _CTC_MACRO_H
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
#define CTC_ETH_ADDR_LEN                 6
#define CTC_MAX_CHIP_NAME_LEN           32

/* define bit operations  */
#define CTC_IS_BIT_SET(flag, bit)   (((flag) & (1 << (bit))) ? 1 : 0)
#define CTC_BIT_SET(flag, bit)      ((flag) = (flag) | (1 << (bit)))
#define CTC_BIT_UNSET(flag, bit)    ((flag) = (flag) & (~(1 << (bit))))

#define CTC_SET_FLAG(VAL, FLAG)          (VAL) = (VAL) | (FLAG)
#define CTC_UNSET_FLAG(VAL, FLAG)        (VAL) = (VAL)&~(FLAG)
#define CTC_FLAG_ISSET(VAL, FLAG)        (((VAL)&(FLAG)) == (FLAG))

/*define make uint32, uint16 operation*/
#define CTC_MAKE_UINT16(hb, lb) (((hb) << 8) | (lb))
#define CTC_MAKE_UINT32(b3, b2, b1, b0) (((b3) << 24) | ((b2) << 16)\
                                       | ((b1) << 8) | (b0))

#define CTC_B2W_SIZE(bits) \
    (((bits) + CTC_UINT32_BITS - 1) / CTC_UINT32_BITS)

/* define bitmap array operation */
/* internal used */
#define _CTC_BMP_OP(_bmp, _offset, _op)     \
    (_bmp[(_offset) / CTC_UINT32_BITS] _op(1U << ((_offset) % CTC_UINT32_BITS)))

/* bmp should be a array of uint32, e.g. uint32 bmp[2] */

/* init bitmap */
#define CTC_BMP_INIT(bmp)                   \
    sal_memset((bmp), 0, sizeof((bmp)));

/* check bitmap */
#define CTC_BMP_OFFSET_CHECK(bmp, offset)   \
    ((0 <= offset) && ((offset) < CTC_BMP_BITS(bmp)))

/* set bit */
#define CTC_BMP_SET(bmp, offset)            \
    _CTC_BMP_OP((bmp), (offset), |= )

/* unset bit */
#define CTC_BMP_UNSET(bmp, offset)          \
    _CTC_BMP_OP((bmp), (offset), &= ~)

/* get bit set */
#define CTC_BMP_ISSET(bmp, offset)          \
    _CTC_BMP_OP((bmp), (offset), &)

/* get bit count */
#define CTC_BMP_BITS(bmp)                   \
    ((CTC_UINT32_BITS * sizeof((bmp)) / sizeof(uint32)))

#define CTC_INTEGER_CMP(data1, data2) \
    { \
        if ((data1) > (data2)) \
        { \
            return 1; \
        } \
        else if ((data1) < (data2)) \
        { \
            return -1; \
        } \
        else \
        { \
        } \
    }

#define CTC_EQUAL_CHECK(item_1, item_2)               \
    {                                                \
        if ((item_1) != (item_2)){                          \
            return CTC_E_INVALID_PARAM;                \
        };                                            \
    }

#define CTC_NOT_EQUAL_CHECK(item_1, item_2)     \
    {                                           \
        if ((item_1) == (item_2)){                     \
            return CTC_E_INVALID_PARAM;            \
        };                                        \
    }

#define CTC_NOT_ZERO_CHECK(item) \
    { \
        if (0 == (item)){ \
            return CTC_E_INVALID_PARAM; \
        } \
    }

#define CTC_PTR_VALID_CHECK(ptr) \
{\
    if ((ptr) == NULL) \
    { \
        return CTC_E_INVALID_PTR; \
    }\
}

/* max value is max valid value */
#define    CTC_MAX_VALUE_CHECK(var, max_value) \
    { \
        if ((var) > (max_value)){return CTC_E_INVALID_PARAM; } \
    }

#define    CTC_MIN_VALUE_CHECK(var, min_value)   \
    { \
        if ((var) < (min_value)){return CTC_E_INVALID_PARAM; } \
    }

#define    CTC_VALUE_RANGE_CHECK(var, min_value, max_value)   \
    { \
        if ((var) < (min_value) || (var) > (max_value)){return CTC_E_INVALID_PARAM; } \
    }

#define CTC_REV_CHECK(val)    \
    { \
        switch (val) \
        { \
        case 0xff: \
        case 0xffff: \
        case 0xffffffff: \
            return CTC_E_INVALID_PARAM; \
        } \
    }

#define CTC_OFFSET_OF(type, member) (intptr)(&((type *)0)->member)

#ifdef SDK_IN_KERNEL
#define CTC_EXPORT_SYMBOL(p_fun) EXPORT_SYMBOL(p_fun)
#else
#define CTC_EXPORT_SYMBOL(p_fun)
#endif

#ifdef __cplusplus
}
#endif

#endif /* _CTC_MACRO_H*/
