#!/usr/bin/env python3

from python_sdk_api.sx_api import *
import struct
import socket
import inspect

DEVICE_ID = 1
SWITCH_ID = 0
ETHERNET_PREFIX = 'Ethernet'
ASIC_MAX_LANES = {SX_CHIP_TYPE_SPECTRUM: 4, SX_CHIP_TYPE_SPECTRUM2: 4, 
                  SX_CHIP_TYPE_SPECTRUM3: 8, SX_CHIP_TYPE_SPECTRUM4: 8}

def sx_open_sdk_connection():
    """ Open connection to SDK
    
    Args:
        None
    
    Returns:
        sx_api_handle_t : SDK handle
    """     
    rc, handle = sx_api_open(None)
    sx_check_rc(rc)
    
    return handle
    
def sx_get_chip_type(handle):
    """ Get system ASIC type
    
    Args:
        handle (sx_api_handle_t): SDK handle
    
    Returns:
        sx_chip_types_t : Chip type
    """       
    try:
        device_info_cnt_p = new_uint32_t_p()
        uint32_t_p_assign(device_info_cnt_p, 1)
        device_info_cnt = uint32_t_p_value(device_info_cnt_p)
        device_info_list_p = new_sx_device_info_t_arr(device_info_cnt)
        
        rc = sx_api_port_device_list_get(handle, device_info_list_p, device_info_cnt_p)
        sx_check_rc(rc)
    
        device_info = sx_device_info_t_arr_getitem(device_info_list_p, 0)
        chip_type = device_info.dev_type
        if chip_type == SX_CHIP_TYPE_SPECTRUM_A1:
            chip_type = SX_CHIP_TYPE_SPECTRUM
            
        return chip_type
    
    finally:
        delete_uint32_t_p(device_info_cnt_p)
        delete_sx_device_info_t_arr(device_info_list_p)

def sx_get_active_vrids(handle):
    """ Get existing virtual router IDs
    
    Args:
        handle (sx_api_handle_t): SDK handle
    
    Returns:
        list : List of virtual routers ids
    """      
    try:
        vrid_list = []
        
        vrid_cnt_p = new_uint32_t_p()
        uint32_t_p_assign(vrid_cnt_p, 0)
        vrid_key_p = new_sx_router_id_t_p()
        sx_router_id_t_p_assign(vrid_key_p, 0)
        vrid_key = sx_router_id_t_p_value(vrid_key_p)
        
        rc = sx_api_router_vrid_iter_get(handle, SX_ACCESS_CMD_GET, vrid_key, None, None, vrid_cnt_p)
        sx_check_rc(rc)
        
        vrid_cnt = uint32_t_p_value(vrid_cnt_p)
        vrid_list_p = new_sx_router_id_t_arr(vrid_cnt)
        
        rc = sx_api_router_vrid_iter_get(handle, SX_ACCESS_CMD_GET_FIRST, vrid_key, None, vrid_list_p, vrid_cnt_p)
        sx_check_rc(rc)
        
        vrid_cnt = uint32_t_p_value(vrid_cnt_p)
        for i in range(0, vrid_cnt):
            vrid = sx_router_id_t_arr_getitem(vrid_list_p, i)
            vrid_list.append(vrid)
            
        return vrid_list
    
    finally:
        delete_uint32_t_p(vrid_cnt_p)
        delete_sx_router_id_t_p(vrid_key_p)
        delete_sx_router_id_t_arr(vrid_list_p)

def sx_get_ports_map(handle):
    """ Get ports map from SDK logical index to SONiC index
    
    Args:
        handle (sx_api_handle_t): SDK handle
    
    Returns:
        dict : Dictionary of ports indices. Key is SDK logical index, value is SONiC index (4 for Ethernet4)
    """         
    try:
        ports_map = {}
        
        # Get chip type
        chip_type = sx_get_chip_type(handle)
        
        # Get ports count
        port_cnt_p = new_uint32_t_p()
        rc = sx_api_port_device_get(handle, DEVICE_ID, SWITCH_ID, None,  port_cnt_p)
        sx_check_rc(rc)
        
        # Get ports
        port_cnt = uint32_t_p_value(port_cnt_p)
        port_attributes_list = new_sx_port_attributes_t_arr(port_cnt)
        rc = sx_api_port_device_get(handle, DEVICE_ID, SWITCH_ID, port_attributes_list,  port_cnt_p)
        sx_check_rc(rc)
        
        for i in range(0, port_cnt):
            port_attributes = sx_port_attributes_t_arr_getitem(port_attributes_list, i)
            label_port = port_attributes.port_mapping.module_port
            logical_port = port_attributes.log_port;
            lane_bmap = port_attributes.port_mapping.lane_bmap;
            
            if (is_phys_port(port_attributes.log_port) == False):
                continue
            
            # Calculate sonic index (sonic index=4 for Ethernet4)
            lane_index = get_lane_index(lane_bmap, ASIC_MAX_LANES[chip_type])
            assert lane_index != -1, "Failed to calculate port index"
            
            sonic_index = label_port * ASIC_MAX_LANES[chip_type] + lane_index;
            sonic_interface = ETHERNET_PREFIX + str(sonic_index)    
            ports_map[logical_port] = sonic_interface
            
        return ports_map
    
    finally:
        delete_uint32_t_p(port_cnt_p)
        delete_sx_port_attributes_t_arr(port_attributes_list)

def sx_router_get_ecmp_id(handle, vrid, ip_prefix):
    """ Get ECMP id for a given IP prefix
    
    Args:
        handle (sx_api_handle_t): SDK handle
        vrid (sx_router_id_t): Virtual router id
        ip_prefix (sx_ip_prefix_t): Network address 
    
    Returns:
        int: ECMP id
    """
    try:
        ip_prefix_p = new_sx_ip_prefix_t_p()
        sx_ip_prefix_t_p_assign(ip_prefix_p, ip_prefix)
        entries_cnt_p = new_uint32_t_p()
        uint32_t_p_assign(entries_cnt_p, 1)
        entries_array = new_sx_uc_route_get_entry_t_arr(1)
        
        rc = sx_api_router_uc_route_get(handle, SX_ACCESS_CMD_GET, vrid, ip_prefix_p, None, entries_array, entries_cnt_p)
        if rc == SX_STATUS_ENTRY_NOT_FOUND:
            return 0
        sx_check_rc(rc)
        
        entry = sx_uc_route_get_entry_t_arr_getitem(entries_array, 0)
        if entry.route_data.type == SX_UC_ROUTE_TYPE_NEXT_HOP:
            return entry.route_data.uc_route_param.ecmp_id
        
        return 0
    
    finally:
        delete_sx_ip_prefix_t_p(ip_prefix_p)
        delete_uint32_t_p(entries_cnt_p)
        delete_sx_uc_route_get_entry_t_arr(entries_array)

def sx_router_operational_ecmp_get(handle, ecmp_id):
    """ Get next hops for a given ECMP id
    
    Args:
        handle (sx_api_handle_t): SDK handle
        ecmp_id (int): ECMP id
    
    Returns:
        list: List of next hops
    """    
    try:
        next_hops = []
        
        next_hop_count_p = new_uint32_t_p()
        uint32_t_p_assign(next_hop_count_p, 0)
        
        rc = sx_api_router_operational_ecmp_get(handle, ecmp_id, None, next_hop_count_p)
        sx_check_rc(rc)
        
        next_hop_count  = uint32_t_p_value(next_hop_count_p)
        next_hop_list_p = new_sx_next_hop_t_arr(next_hop_count)
        
        rc = sx_api_router_operational_ecmp_get(handle, ecmp_id, next_hop_list_p, next_hop_count_p)
        sx_check_rc(rc)
        
        next_hop_count  = uint32_t_p_value(next_hop_count_p)
        for i in range(next_hop_count):
            next_hop = sx_next_hop_t_arr_getitem(next_hop_list_p, i)
            if next_hop.next_hop_key.type == SX_NEXT_HOP_TYPE_IP:
                next_hops.append(next_hop)
                
        return next_hops
    
    finally:
        delete_uint32_t_p(next_hop_count_p)
        delete_sx_next_hop_t_arr(next_hop_list_p)

def sx_get_router_interface(handle, vrid, rif):
    """ Get router interface information
    
    Args:
        handle (sx_api_handle_t): SDK handle
        vrid (sx_router_id_t): virtual router id
        rif (sx_router_interface_t): router interface id
    
    Returns:
        dict : Dictionary contains interface parameters
    """       
    try:
        vrid_p = new_sx_router_id_t_p()
        sx_router_id_t_p_assign(vrid_p, vrid)
    
        ifc_p = new_sx_router_interface_param_t_p()
        ifc_attr_p = new_sx_interface_attributes_t_p()
        rif_params = {}
        
        rc = sx_api_router_interface_get(handle, rif, vrid_p, ifc_p, ifc_attr_p)
        sx_check_rc(rc)
        
        if ifc_p.type == SX_L2_INTERFACE_TYPE_PORT_VLAN:
            rif_params['port'] = ifc_p.ifc.port_vlan.port
            
        if ifc_p.type == SX_L2_INTERFACE_TYPE_VPORT:
            rif_params['vport'] = ifc_p.ifc.vport.vport        
    
        if ifc_p.type == SX_L2_INTERFACE_TYPE_VLAN:
            rif_params['vlan'] = ifc_p.ifc.vlan.vlan
            
        return rif_params
        
    finally:
        delete_sx_router_id_t_p(vrid_p)
        delete_sx_router_interface_param_t_p(ifc_p)
        delete_sx_interface_attributes_t_p(ifc_attr_p)    

def sx_port_vport_base_get(handle, vport):
    """ Get SDK logical index for given vport
    
    Args:
        handle (sx_api_handle_t): SDK handle
        vport (sx_port_id_t): SDK vport id

    Returns:
        sx_port_log_id_t : SDK logical index 
    """      
    try:
        vlan_id_p = new_sx_vlan_id_t_p()
        logical_port_p = new_sx_port_log_id_t_p()
        
        rc = sx_api_port_vport_base_get(handle, vport, vlan_id_p, logical_port_p)
        sx_check_rc(rc)
        
        logical_port = sx_port_log_id_t_p_value(logical_port_p)
        
        return logical_port  
      
    finally:
        delete_sx_vlan_id_t_p(vlan_id_p)
        delete_sx_port_log_id_t_p(logical_port_p)   
        
def sx_router_neigh_get_mac(handle, rif, addr, type_ipv6=False):
    """ Get neighbour mac address
    
    Args:
        handle (sx_api_handle_t): SDK handle
        rif (sx_port_id_t): SDK vport id
        addr (sx_ip_addr_t): Neighbour IP address
        type_ipv6 (bool): True for IPv6

    Returns:
        str : Neighbour mac address
    """     
    try:
        neigh_entry_cnt_p = new_uint32_t_p()
        neigh_entry_list_p = new_sx_neigh_get_entry_t_arr(1)

        filter_p = new_sx_neigh_filter_t_p()
        neigh_filter = sx_neigh_filter_t()
        neigh_filter.filter_by_rif = SX_KEY_FILTER_FIELD_NOT_VALID
        neigh_filter.rif = 0
        sx_neigh_filter_t_p_assign(filter_p, neigh_filter)
        
        rc = sx_api_router_neigh_get(handle, SX_ACCESS_CMD_GET, rif, addr, filter_p, neigh_entry_list_p, neigh_entry_cnt_p)
        sx_check_rc(rc)

        neighbor_entry = sx_neigh_get_entry_t_arr_getitem(neigh_entry_list_p, 0)
        
        return neighbor_entry.neigh_data.mac_addr.to_str()
    
    finally:
        delete_sx_neigh_filter_t_p(filter_p)
        delete_uint32_t_p(neigh_entry_cnt_p)
        delete_sx_neigh_get_entry_t_arr(neigh_entry_list_p)    
        
        
def sx_fdb_uc_mac_addr_get(handle, vlan_id, mac_addr):
    """ Get UC mac entry from FDB
    
    Args:
        handle (sx_api_handle_t): SDK handle
        vlan_id (sx_vlan_id_t): VLAN id
        mac_addr (str): mac address

    Returns:
        sx_fdb_uc_mac_addr_params_t : FDB mac entry
    """       
    try:
        key = sx_fdb_uc_mac_addr_params_t()
        key.fid_vid = vlan_id
        key.mac_addr = ether_addr(mac_addr)
        key.entry_type = SX_FDB_UC_AGEABLE
        key.action = SX_FDB_ACTION_FORWARD
        key_p = copy_sx_fdb_uc_mac_addr_params_t_p(key)
        
        key_filter = sx_fdb_uc_key_filter_t()
        key_filter.filter_by_fid =  SX_FDB_KEY_FILTER_FIELD_VALID
        key_filter.filter_by_mac_addr = SX_FDB_KEY_FILTER_FIELD_VALID
        key_filter.filter_by_log_port = SX_FDB_KEY_FILTER_FIELD_NOT_VALID
        key_filter.fid = vlan_id
        key_filter.mac_addr = ether_addr(mac_addr)
        key_filter_p = copy_sx_fdb_uc_key_filter_t_p(key_filter)
    
        data_cnt_p = copy_uint32_t_p(SX_FDB_MAX_GET_ENTRIES)
        mac_list_p = new_sx_fdb_uc_mac_addr_params_t_arr(SX_FDB_MAX_GET_ENTRIES)
        
        rc = sx_api_fdb_uc_mac_addr_get(handle, 0, SX_ACCESS_CMD_GET_FIRST, SX_FDB_UC_AGEABLE, key_p, key_filter_p, mac_list_p, data_cnt_p)
        sx_check_rc(rc)
        
        data_cnt = uint32_t_p_value(data_cnt_p)
        assert data_cnt == 1, "Got unexpected macs amount, mac {} vlan {}".format(mac_addr, vlan_id)
        
        mac_entry = sx_fdb_uc_mac_addr_params_t_arr_getitem(mac_list_p, 0)
        assert mac_entry.dest_type == SX_FDB_UC_MAC_ADDR_DEST_TYPE_LOGICAL_PORT, "Got unexpected mac entry type {}".format(mac_entry.dest_type)

        return mac_entry

    finally:
        delete_sx_fdb_uc_key_filter_t_p(key_filter_p)
        delete_sx_fdb_uc_mac_addr_params_t_p(key_p)
        delete_sx_fdb_uc_mac_addr_params_t_arr(mac_list_p)
        delete_uint32_t_p(data_cnt_p)       
        
def sx_lag_port_group_get(handle, lag_id):
    """ Get LAG members
    
    Args:
        handle (sx_api_handle_t): SDK handle
        lag_id (sx_port_log_id_t): LAG id

    Returns:
        list : list of LAG members logical indices
    """      
    try:
        lag_members = []
        port_count_p = copy_uint32_t_p(0)
        port_arr = None
    
        rc = sx_api_lag_port_group_get(handle, 0, lag_id, port_arr, port_count_p)
        sx_check_rc(rc)
        
        port_count = uint32_t_p_value(port_count_p)
        if port_count > 0:
            port_arr = new_sx_port_log_id_t_arr(port_count)
            rc = sx_api_lag_port_group_get(handle, 0, lag_id, port_arr, port_count_p)
            sx_check_rc(rc)
            
            for i in range(port_count):
                lag_members.append(sx_port_log_id_t_arr_getitem(port_arr, i))
                                
        return lag_members
    
    finally:
        delete_uint32_t_p(port_count_p)
        delete_sx_port_log_id_t_arr(port_arr) 
                  
def sx_check_rc(rc):
    if rc is not SX_STATUS_SUCCESS:
        # Get the calling function name from the last frame
        cf = inspect.currentframe().f_back
        func_name = inspect.getframeinfo(cf).function
        error_info = func_name + ' failed with rc = ' + str(rc)
    
        raise Exception(error_info)

def sx_make_ip_prefix_v4(addr, mask):
    """ Create IPv4 prefix
    
    Args:
        addr (str): IPv4 address
        mask (str): Network mask

    Returns:
        sx_ip_prefix_t : IPv4 prefix
    """       
    ip_prefix = sx_ip_prefix_t()
    ip_prefix.version = SX_IP_VERSION_IPV4
    ip_prefix.prefix.ipv4.addr.s_addr = struct.unpack('>I', socket.inet_pton(socket.AF_INET, addr))[0]
    ip_prefix.prefix.ipv4.mask.s_addr = struct.unpack('>I', socket.inet_pton(socket.AF_INET, mask))[0]
    
    return ip_prefix

def sx_make_ip_prefix_v6(addr, mask):
    """ Create IPv6 prefix
    
    Args:
        addr (str): IPv6 address
        mask (str): Network mask

    Returns:
        sx_ip_v6_prefix_t : IPv6 prefix
    """         
    prefix = sx_ip_v6_prefix_t()
    ip_prefix = sx_ip_prefix_t()
    ip_prefix.version = SX_IP_VERSION_IPV6
    ip_prefix.prefix = prefix
    
    for i in range(0, 16):
        uint8_t_arr_setitem(ip_prefix.prefix.ipv6.addr._in6_addr__in6_u._in6_addr___in6_u__u6_addr8, i, addr[i])
        uint8_t_arr_setitem(ip_prefix.prefix.ipv6.mask._in6_addr__in6_u._in6_addr___in6_u__u6_addr8, i, mask[i])
        
    return ip_prefix

def get_lane_index(lane_bmap, max_lanes):
    """ Get index of first lane in use (2 for 00001100)
    
    Args:
        lane_bmap (int): bitmap indicating module lanes in use
        max_lanes (int): Max lanes in module

    Returns:
        int : index of the first bit set to 1 in lane_bmap
    """       
    for lane_idx in range(0, max_lanes):
        if (lane_bmap & 0x1 == 1):
            return lane_idx
        lane_bmap = lane_bmap >> 1
    return -1  

def get_port_type(log_port_id):
    return (log_port_id & SX_PORT_TYPE_ID_MASK) >> SX_PORT_TYPE_ID_OFFS

def is_phys_port(log_port_id):
    return get_port_type(log_port_id) == SX_PORT_TYPE_NETWORK

def is_lag(log_port_id):
    return get_port_type(log_port_id) == SX_PORT_TYPE_LAG
 
 