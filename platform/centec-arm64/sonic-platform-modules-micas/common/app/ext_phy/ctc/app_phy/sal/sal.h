#ifndef __SAL_H__
#define __SAL_H__

/**
 * @file kal.h
 */

#include "sal_types.h"

#define _SAL_DEBUG
#if defined(_SAL_LINUX_KM)
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/string.h>
#include <linux/errno.h>
#include <linux/interrupt.h>
#include <linux/semaphore.h>
#include <linux/ctype.h>
#include <linux/fcntl.h>
#include <linux/sched.h>
#include <linux/random.h>
#include <linux/spinlock.h>
#elif defined(_SAL_LINUX_UM)
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/time.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <ctype.h>
#include <sys/mman.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <errno.h>
#include <ctype.h>
#include <semaphore.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <linux/if_ether.h>
#include <linux/sockios.h>
#include <netpacket/packet.h>
#include <sys/un.h>
#include <time.h>
#include <signal.h>
#endif

#include "phy_platformroutines.h"

#define sal_printf  printf

#define BOOLEAN_BIT(b) ((b) ? 1 : 0)

#undef sal_memcmp
#define sal_memcmp   memcmp

#undef sal_memmove
#define sal_memmove  memmove
/*string*/
#undef sal_vprintf
#define sal_vprintf vprintf

#undef sal_sprintf
#define sal_sprintf sprintf

#undef sal_sscanf
#define sal_sscanf sscanf

#undef sal_strcpy
#define sal_strcpy strcpy

#undef sal_strncpy
#define sal_strncpy strncpy

#undef sal_strcat
#define sal_strcat strcat

#undef sal_strncat
#define sal_strncat strncat

#undef sal_strcmp
#define sal_strcmp strcmp

#undef sal_strncmp
#define sal_strncmp strncmp

#undef sal_strlen
#define sal_strlen strlen

#undef sal_snprintf
#define sal_snprintf snprintf

#undef sal_vsnprintf
#define sal_vsnprintf vsnprintf

#undef sal_vsprintf
#define sal_vsprintf vsprintf

#undef sal_strtos32
#undef sal_strtou32
#undef sal_strtou64
#undef sal_atoi
#undef sal_strtol
#undef sal_strtol
#if defined(_SAL_LINUX_KM)
#define sal_strtou32(x, y, z) simple_strtoul((char*)x, (char**)y, z)
#define sal_strtos32(x, y, z) simple_strtol((char*)x, (char**)y, z)
#define sal_strtou64(x, y, z) simple_strtoull((char*)x, (char**)y, z)
#define sal_atoi(x) simple_strtol((char*)x, NULL, 10)
#define sal_strtol(x, y, z) simple_strtol((char*)x, (char**)y, z)
#define sal_strtok(x, y) strsep((char**)&x, y)

#else
#define sal_atoi atoi
#define sal_strtos32(x, y, z) strtol((char*)x, (char**)y, z)
#define sal_strtou32(x, y, z) strtoul((char*)x, (char**)y, z)
#define sal_strtol strtol

#undef sal_rand
#define sal_rand rand

#undef sal_srand
#define sal_srand srand

/*memory */
#undef sal_malloc
#define sal_malloc   malloc

#undef sal_realloc
#define sal_realloc realloc

#undef sal_free
#define sal_free   free

#undef sal_time
#define sal_time time

#undef sal_ctime
#define sal_ctime ctime

#undef sal_strtok
#define sal_strtok strtok

#endif

#if defined (_SAL_LINUX_UM)
#define sal_strtou64(x, y, z) strtoull((char*)x, (char**)y, z)
#endif

#undef sal_strchr
#define sal_strchr strchr

#undef sal_strstr
#define sal_strstr strstr

#undef sal_strrchr
#define sal_strrchr strrchr

#undef sal_strspn
#define sal_strspn strspn

#undef sal_strerror
#define sal_strerror strerror

#undef sal_strsep
#define sal_strsep strsep

#undef sal_strtok_r
#define sal_strtok_r strtok_r

#undef sal_tolower
#undef sal_toupper
#define sal_tolower tolower
#define sal_toupper toupper

#undef sal_isspace
#undef sal_isdigit
#undef sal_isxdigit
#undef sal_isalpha
#undef sal_isalnum
#undef sal_isupper
#undef sal_islower
#define sal_isspace isspace
#define sal_isdigit isdigit
#define sal_isxdigit isxdigit
#define sal_isalpha isalpha
#define sal_isalnum isalnum
#define sal_isupper isupper
#define sal_islower islower
#define sal_isprint isprint

#undef sal_ntohl
#undef sal_htonl
#undef sal_ntohs
#undef sal_htons

#define sal_ntohl ntohl
#define sal_htonl htonl
#define sal_ntohs ntohs
#define sal_htons htons

#undef sal_memcpy
#undef sal_memset
#define sal_memcpy    memcpy
#define sal_memset    memset

#ifdef _SAL_LINUX_UM

#undef sal_strcasecmp
#define sal_strcasecmp strcasecmp

#undef sal_strncasecmp
#define sal_strncasecmp strncasecmp

#undef sal_inet_pton
#define sal_inet_pton inet_pton

#undef sal_inet_ntop
#define sal_inet_ntop inet_ntop

#undef sal_ioctl
#define sal_ioctl ioctl

#endif

#if defined (_SAL_LINUX_UM) || defined (_SAL_VXWORKS)
#undef sal_qsort
#define sal_qsort qsort
#endif

#define SET_BIT(flag, bit)      (flag) = (flag) | (1 << (bit))
#define CLEAR_BIT(flag, bit)    (flag) = (flag) & (~(1 << (bit)))
#define IS_BIT_SET(flag, bit)   (((flag) & (1 << (bit))) ? 1 : 0)

#define SET_BIT_RANGE(dst, src, s_bit, len) \
    { \
        uint8 i = 0; \
        for (i = 0; i < len; i++) \
        { \
            if (IS_BIT_SET(src, i)) \
            { \
                SET_BIT(dst, (s_bit + i)); \
            } \
            else \
            { \
                CLEAR_BIT(dst, (s_bit + i)); \
            } \
        } \
    }

#ifdef _SAL_VXWORKS
#define PTR_TO_INT(x)       ((uint32)(((uint32)(x)) & 0xFFFFFFFF))
#define INT_TO_PTR(x)       ((void*)(uint32)(x))

#ifndef AF_INET6
#define AF_INET6    10  /* IP version 6 */
#endif

#endif

#ifdef _SAL_LINUX_KM
#ifndef AF_INET6
#define AF_INET6    10  /* IP version 6 */
#endif

#ifndef AF_INET
#define AF_INET    9  /* IP version 4 */
#endif

#endif

#ifdef __cplusplus
extern "C" {
#endif

/* sal_file define */
#if defined(_SAL_LINUX_KM)
#define sal_open ctc_sal_open
#define sal_fopen ctc_sal_fopen
#define sal_fclose ctc_sal_fclose
#define sal_read ctc_sal_read
#define sal_write ctc_sal_write
#define sal_fgets ctc_sal_fgets
#define sal_eof ctc_sal_eof
#define sal_fseek ctc_sal_fseek
#define sal_ftell ctc_sal_ftell
#define sal_fwrite(buff, len, count, ft)    ctc_sal_write(ft, buff, (count)*(len))
#define sal_fread(buff, len, count, ft)    ctc_sal_read(ft, buff, (count)*(len))
#define sal_feof ctc_sal_eof
#else
/* linux user and vxworks file operation */
#undef sal_open
#define sal_open open

#undef sal_close
#define sal_close close

#undef sal_fopen
#define sal_fopen fopen

#undef sal_fclose
#define sal_fclose fclose

#undef sal_read
#define sal_read read

#undef sal_write
#define sal_write write

#undef sal_fread
#define sal_fread fread

#undef sal_fwrite
#define sal_fwrite fwrite

#undef sal_fprintf
#define sal_fprintf fprintf

#undef sal_fgets
#define sal_fgets fgets

#undef sal_fseek
#define sal_fseek fseek

#undef sal_ftell
#define sal_ftell ftell

#undef sal_feof
#define sal_feof feof

#endif

#define sal_udelay ctc_sal_udelay
#define sal_delay ctc_sal_delay

#ifdef __cplusplus
}
#endif

#endif /* !__SAL_H__ */
