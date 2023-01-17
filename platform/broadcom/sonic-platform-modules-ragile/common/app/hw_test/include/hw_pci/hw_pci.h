/**
 * Copyright(C) 2010 Ruijie Network. All rights reserved.
 */
/*
 * hw_pci.h
 * Original Author : liangeb@ruijie.com.cn, 2012-07-26
 *
 * pci/pcie HardWare test definitions
 *
 * History
 *    v1.0    enbo liang(liangeb@ruijie.com.cn)  2012-07-26  Initial version.
 */
#ifndef _HW_PCI_H
#define _HW_PCI_H

struct pci_dev_priv {
    int pcibus;
    int slot;
    int fn;
    int bar;
    int offset;
    unsigned int data;
    int times;
    unsigned int check_test_errors;
};

#define PCI_MAX_NAME_SIZE          256


extern int pci_wr_main(int argc, char **argv);
extern int pci_rd_main(int argc, char **argv);
extern int pci_dump_main(int argc, char **argv);
extern int pci_cfg_wr_main(int argc, char **argv);
extern int pci_cfg_rd_main(int argc, char **argv);
extern int pci_chk_main(int argc, char **argv);

#endif /* _HW_PCI_H */

