/*
 * Copyright 2019 Broadcom. All rights reserved.
 * The term “Broadcom” refers to Broadcom Inc. and/or its subsidiaries.
 *
 * Description
 *  Platform system status module structures
 */

#ifndef __PDDF_SYSSTATUS_DEFS_H__
#define __PDDF_SYSSTATUS_DEFS_H__


#define ATTR_NAME_LEN 32
#define MAX_ATTRS 32


/* SYSSTATUS CLIENT DATA - PLATFORM DATA FOR SYSSTATUS CLIENT */
typedef struct SYSSTATUS_ADDR_ATTR
{
    char aname[ATTR_NAME_LEN];  // attr name
    uint32_t devaddr;
    uint32_t offset;
    uint32_t mask;
    uint32_t len;

}SYSSTATUS_ADDR_ATTR;


typedef struct SYSSTATUS_DATA
{
  int len;
  SYSSTATUS_ADDR_ATTR sysstatus_addr_attr;
  SYSSTATUS_ADDR_ATTR sysstatus_addr_attrs[MAX_ATTRS]; 
  
}SYSSTATUS_DATA;




#endif //__PDDF_SYSSTATUS_DEFS_H__        
