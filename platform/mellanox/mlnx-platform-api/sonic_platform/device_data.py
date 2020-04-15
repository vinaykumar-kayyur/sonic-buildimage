DEVICE_DATA = {
    'x86_64-mlnx_msn2700-r0': {
        'thermal': {
            'minimum_table': {
                "p2c_trust":   {"-127:40":13, "41:120":15},
                "p2c_untrust": {"-127:25":13, "26:30":14 , "31:35":15, "36:120":16},
                "c2p_trust":   {"-127:20":13, "21:25":14 , "26:30":15, "31:120":16},
                "c2p_untrust": {"-127:20":13, "21:25":14 , "26:30":15, "31:120":16},
                "unk_trust":   {"-127:20":13, "21:25":14 , "26:30":15, "31:120":16},
                "unk_untrust": {"-127:20":13, "21:25":14 , "26:30":15, "31:120":16}
            }
        },
        'fans': {
            'drawer_num': 4,
            'drawer_type': 'real',
            'fan_num_per_drawer': 2,
            'support_fan_direction': False,
            'hot_swappable': True
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': True,
            'led_num': 1
        }
    },
    'x86_64-mlnx_msn2740-r0': {
        'thermal': {
            'minimum_table': {
                "p2c_trust":   {"-127:120":13},
                "p2c_untrust": {"-127:35":13, "36:40":14 , "41:120":15},
                "c2p_trust":   {"-127:120":13},
                "c2p_untrust": {"-127:15":13, "16:30":14 , "31:35":15, "36:120":17},
                "unk_trust":   {"-127:120":13},
                "unk_untrust": {"-127:15":13, "16:30":14 , "31:35":15, "36:120":17},
            }
        },
        'fans': {
            'drawer_num': 4,
            'drawer_type': 'real',
            'fan_num_per_drawer': 1,
            'support_fan_direction': False,
            'hot_swappable': True
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': True,
            'led_num': 1
        }
    },
    'x86_64-mlnx_msn2100-r0': {
        'thermal': {
            'minimum_table': {
                "p2c_trust":  {"-127:120":12},
                "p2c_untrust": {"-127:15":12, "16:25":13, "26:30":14, "31:35":15, "36:120":16},
                "c2p_trust":   {"-127:40":12, "41:120":13},
                "c2p_untrust": {"-127:40":12, "41:120":13},
                "unk_trust":   {"-127:40":12, "41:120":13},
                "unk_untrust": {"-127:15":12, "16:25":13, "26:30":14, "31:35":15, "36:120":16}
            }
        },
        'fans': {
            'drawer_num': 1,
            'drawer_type': 'virtual',
            'fan_num_per_drawer': 4,
            'support_fan_direction': False,
            'hot_swappable': False
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': False,
            'led_num': 2
        }
    },
    'x86_64-mlnx_msn2410-r0': {
        'thermal': {
            'minimum_table': {
                "p2c_trust":   {"-127:40":13, "41:120":15},
                "p2c_untrust": {"-127:25":13, "26:30":14 , "31:35":15, "36:120":16},
                "c2p_trust":   {"-127:20":13, "21:25":14 , "26:30":15, "31:120":16},
                "c2p_untrust": {"-127:20":13, "21:25":14 , "26:30":15, "31:120":16},
                "unk_trust":   {"-127:20":13, "21:25":14 , "26:30":15, "31:120":16},
                "unk_untrust": {"-127:20":13, "21:25":14 , "26:30":15, "31:120":16}
            }
        },
        'fans': {
            'drawer_num': 4,
            'drawer_type': 'real',
            'fan_num_per_drawer': 2,
            'support_fan_direction': False,
            'hot_swappable': True
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': True,
            'led_num': 1
        }
    },
    'x86_64-mlnx_msn2010-r0': {
        'thermal': {
            'minimum_table': {
                "p2c_trust":   {"-127:120":12},
                "p2c_untrust": {"-127:15":12, "16:20":13, "21:30":14, "31:35":15, "36:120":16},
                "c2p_trust":   {"-127:120":12},
                "c2p_untrust": {"-127:20":12, "21:25":13 , "26:30":14, "31:35":15, "36:120":16},
                "unk_trust":   {"-127:120":12},
                "unk_untrust": {"-127:15":12, "16:20":13 , "21:30":14, "31:35":15, "36:120":16}
            }
        },
        'fans': {
            'drawer_num': 1,
            'drawer_type': 'virtual',
            'fan_num_per_drawer': 4,
            'support_fan_direction': False,
            'hot_swappable': False
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': False,
            'led_num': 2
        }
    },
    'x86_64-mlnx_msn3700-r0': {
        'thermal': {
            'minimum_table': {
                "p2c_trust":   {"-127:25":12, "26:40":13 , "41:120":14},
                "p2c_untrust": {"-127:15":12, "16:30":13 , "31:35":14, "36:40":15, "41:120":16},
                "c2p_trust":   {"-127:25":12, "26:40":13 , "41:120":14},
                "c2p_untrust":   {"-127:25":12, "26:40":13 , "41:120":14},
                "unk_trust":   {"-127:25":12, "26:40":13 , "41:120":14},
                "unk_untrust": {"-127:15":12, "16:30":13 , "31:35":14, "36:40":15, "41:120":16},
            }
        },
        'fans': {
            'drawer_num': 6,
            'drawer_type': 'real',
            'fan_num_per_drawer': 2,
            'support_fan_direction': True,
            'hot_swappable': True
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': True,
            'led_num': 1
        }
    },
    'x86_64-mlnx_msn3700c-r0': {
        'thermal': {
            'minimum_table': {
                "p2c_trust":   {"-127:25":12, "26:40":13 , "41:120":14},
                "p2c_untrust": {"-127:15":12, "16:30":13 , "31:35":14, "36:40":15, "41:120":16},
                "c2p_trust":   {"-127:25":12, "26:40":13 , "41:120":14},
                "c2p_untrust":   {"-127:25":12, "26:40":13 , "41:120":14},
                "unk_trust":   {"-127:25":12, "26:40":13 , "41:120":14},
                "unk_untrust": {"-127:15":12, "16:30":13 , "31:35":14, "36:40":15, "41:120":16},
            }
        },
        'fans': {
            'drawer_num': 4,
            'drawer_type': 'real',
            'fan_num_per_drawer': 2,
            'support_fan_direction': True,
            'hot_swappable': True
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': True,
            'led_num': 1
        }
    },
    'x86_64-mlnx_msn3800-r0': {
        'thermal': {
            'minimum_table': {
                "p2c_trust":   {"-127:35":12, "36:120":13},
                "p2c_untrust": {"-127:0":12, "1:10":13 , "11:15":14, "16:20":15, "21:35":16, "36:120":17},
                "c2p_trust":   {"-127:30":12, "31:40":13 , "41:120":14},
                "c2p_untrust":   {"-127:20":12, "21:30":13 , "31:35":14, "36:40":15, "41:120":16},
                "unk_trust":   {"-127:30":12, "31:40":13 , "41:120":14},
                "unk_untrust": {"-127:0":12, "1:10":13 , "11:15":14, "16:20":15, "21:35":16, "36:120":17},
            }
        },
        'fans': {
            'drawer_num': 3,
            'drawer_type': 'real',
            'fan_num_per_drawer': 1,
            'support_fan_direction': True,
            'hot_swappable': True
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': True,
            'led_num': 1
        }
    },
    'x86_64-mlnx_msn4700-r0': {
        'fans': {
            'drawer_num': 6,
            'drawer_type': 'real',
            'fan_num_per_drawer': 2,
            'support_fan_direction': True,
            'hot_swappable': True
        },
        'psus': {
            'psu_num': 2,
            'fan_num_per_psu': 1,
            'hot_swappable': True,
            'led_num': 1
        }
    }
}