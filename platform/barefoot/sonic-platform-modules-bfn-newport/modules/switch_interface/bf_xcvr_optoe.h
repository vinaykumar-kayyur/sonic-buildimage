/*
 * Copyright (c) 2021 Edgecore Networks Corporation
 *
 * This file is licensed under the terms of the GNU General Public
 * License version 2. This program is licensed "as is" without any
 * warranty of any kind, whether express or implied.
 *
 * xcvr driver optoe related data structures and functions
 */

#ifndef __BF_XCVR_OPTOE_H__
#define __BF_XCVR_OPTOE_H__

int optoe_probe(struct platform_device *pdev, struct optoe_data *optoe);
void optoe_remove(struct optoe_data *optoe);

#endif //__BF_XCVR_OPTOE_H__
