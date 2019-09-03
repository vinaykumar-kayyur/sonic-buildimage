//port info

//i2c_eeprom_config_cypress
#ifndef __PORT_INFO_CONFIG_BANYAN
#define __PORT_INFO_CONFIG_BANYAN

struct port_info_map_t banyan_port_info_map[] = {

    {0, QSFP_DD_TYPE, "0"},
    {1, QSFP_DD_TYPE, "1"},
    {2, QSFP_DD_TYPE, "2"},
    {3, QSFP_DD_TYPE, "3"},
    {4, QSFP_DD_TYPE, "4"},
    {5, QSFP_DD_TYPE, "5"},
    {6, QSFP_DD_TYPE, "6"},
    {7, QSFP_DD_TYPE, "7"},

    {8, QSFP_DD_TYPE, "8"},
    {9, QSFP_DD_TYPE, "9"},
    {10, QSFP_DD_TYPE,"10"},
    {11, QSFP_DD_TYPE, "11"},
    {12, QSFP_DD_TYPE, "12"},
    {13, QSFP_DD_TYPE, "13"},
    {14, QSFP_DD_TYPE, "14"},
    {15, QSFP_DD_TYPE, "15"},

    {16, QSFP_DD_TYPE, "16"},
    {17, QSFP_DD_TYPE, "17"},
    {18, QSFP_DD_TYPE, "18"},
    {19, QSFP_DD_TYPE, "19"},
    {20, QSFP_DD_TYPE, "20"},
    {21, QSFP_DD_TYPE, "21"},
    {22, QSFP_DD_TYPE, "22"},
    {23, QSFP_DD_TYPE, "23"},

    {24, QSFP_DD_TYPE, "24"},
    {25, QSFP_DD_TYPE, "25"},
    {26, QSFP_DD_TYPE, "26"},
    {27, QSFP_DD_TYPE, "27"},
    {28, QSFP_DD_TYPE, "28"},
    {29, QSFP_DD_TYPE, "29"},
    {30, QSFP_DD_TYPE, "30"},
    {31, QSFP_DD_TYPE, "31"},
};

struct port_info_table_t banyan_port_info_table =
{
    .map =  banyan_port_info_map,
    .size = ARRAY_SIZE(banyan_port_info_map),
};

#endif /*__PORT_INFO_CONFIG_BANYAN*/
