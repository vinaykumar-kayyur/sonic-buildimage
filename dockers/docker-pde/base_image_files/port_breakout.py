#! /usr/bin/python -u

import os
import sys
import re
import getopt
import copy
import json
import shutil

SIM_HOST = False

if not SIM_HOST:
    import subprocess

    import click

    import sonic_device_util
    """
    from sonic_platform import get_machine_info
    from sonic_platform import get_platform_info
    """
    from swsssdk import ConfigDBConnector

SAI_PROFILE_DELIMITER = '='
INTERFACE_KEY="Ethernet"
if not SIM_HOST:
    NEW_FILE_EXT=""
else:
    NEW_FILE_EXT=""

#####################################################################################################
### Platform related code

if not SIM_HOST:
    def get_platform():
        ###
        ### This function is used to get the HW info helper function
        ###
        machine_info = sonic_device_util.get_machine_info()
        return sonic_device_util.get_platform_info(machine_info)
        """
        return get_platform_info(get_machine_info())
        """


    def get_hwsku():
        config_db = ConfigDBConnector()
        config_db.connect()
        data = config_db.get_table('DEVICE_METADATA')
        try:
            hwsku = data['localhost']['hwsku']
        except KeyError:
            hwsku = "Unknown"
        return hwsku

    def get_pde_hwsku(platform):
        cmd = "cat /usr/share/sonic/device/" + platform + "/default_sku | cut -d ' ' -f 1"
        pin = subprocess.Popen(cmd,
                               shell=True,
                               close_fds=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        id = pin.communicate()[0]
        id = id.strip()
        print id
        return id


    # run command
    def run_command(command, display_cmd=False, ignore_error=False, print_to_console=True):
        ###
        ### Run bash command and print output to stdout
        ###
        if display_cmd == True:
            click.echo(click.style("Running command: ", fg='cyan') + click.style(command, fg='green'))

        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        (out, err) = proc.communicate()

        if len(out) > 0 and print_to_console:
            click.echo(out)

        if proc.returncode != 0 and not ignore_error:
            sys.exit(proc.returncode)

        return out, err

    def get_bcm_file(platform, hwsku):
        sai_profile_kvs = {}

        sai_file = "/usr/share/sonic/device/" + platform + "/" + hwsku + "/" + "sai.profile"
        command = "cat "+ sai_file
        sai_profile_content, _ = run_command(command, print_to_console=False)

        for line in sai_profile_content.split('\n'):
            if not SAI_PROFILE_DELIMITER in line:
                continue
            key, value = line.split(SAI_PROFILE_DELIMITER)
            sai_profile_kvs[key] = value.strip()

        try:
            sai_xml_path = sai_profile_kvs['SAI_INIT_CONFIG_FILE']
        except KeyError:
            print >> sys.stderr, "Failed to get SAI XML from sai profile"
            sys.exit(1)

        return "/usr/share/sonic/device/" + platform + "/" + hwsku + "/" + os.path.basename(sai_xml_path)

#####################################################################################################


def get_ini_file(platform, hwsku):
    ini_file = "/usr/share/sonic/device/" + platform + '/' + hwsku + '/' + "port_config.ini"
    return ini_file

def get_cfg_file(platform, hwsku):
    cfg_file = "/etc/sonic/config_db.json"
    return cfg_file


def display_files(platform, hwsku):
    print("BCM File:[%s]" % (get_bcm_file(platform, hwsku)))
    print("INI File:[%s]" % (get_ini_file(platform, hwsku)))
    print("CFG File:[%s]" % (get_cfg_file(platform, hwsku)))

 
bko_dict = {
    "1x100": { "lanes":4, "speed":100, "step":4, "bko":0, "name": "hundredGigE" },
    "1x40":  { "lanes":4, "speed":40,  "step":4, "bko":0, "name": "fourtyGigE" },
    "4x10":  { "lanes":4, "speed":10,  "step":1, "bko":1, "name": "tenGigE" },
    "4x25":  { "lanes":4, "speed":25,  "step":1, "bko":1, "name": "twentyfiveGigE" },
}

#
#   Get breakout step:
#
def bko_opt_valid(opt):
    if opt in bko_dict:
        return True
    else:
        return False

def get_bkout_step(opt):
    return bko_dict[opt]["step"]

def get_bkout_subport_name(opt):
    return bko_dict[opt]["name"]

def get_bkout_subport_speed(opt):
    return bko_dict[opt]["speed"]

def get_is_bkout(opt):
    return bko_dict[opt]["bko"]

def get_bkout_lanes(opt):
    return bko_dict[opt]["lanes"]

def get_bkout_ports(port, opt):
    lanes = bko_dict[opt]["lanes"]
    step  = get_bkout_step(opt)

    if not port.startswith(INTERFACE_KEY):
        return None

    idx   = port.split()[0].split(INTERFACE_KEY,1)[1]
    if not idx.isdigit():
        return None

    ports = []
    for i in range(0, lanes, 1):
        portx = INTERFACE_KEY + str(int(idx) + i)
        ports.append(portx)
    return ports


#
#   Breakout a port in INI file:
#   Ethernet48       81,82,83,84           hundredGigE13

#   Change to
#   Ethernet48       81           twentyfiveGigE13:1
#   Ethernet49       82           twentyfiveGigE13:2
#   Ethernet50       83           twentyfiveGigE13:3
#   Ethernet51       84           twentyfiveGigE13:4

#
#   Ethernet48      81,82,83,84           hundredGigE13
#   return:
#      "48"
#      ["81", "82", "83", "84"]
#      "hundredGigE"
#      "13"


def get_info_in_ini(line, title):
    idx = line.split()[0].split(INTERFACE_KEY,1)[1]
    lanes = line.split()[1].split(",")
    name = line.split()[2]
    temp = name.split(":")[0]
    porti = re.sub('.*?([0-9]*)$',r'\1', temp)

    if "index" in title:
        fp_idx = int(line.split()[title.index("index")])
    else:
        fp_idx = None
    return idx, lanes, name, porti, fp_idx

def break_in_ini(port, ini_file, opt):
    print("Breaking port %s to %s in ini ..." % (port, opt))

    bak_file = ini_file + ".bak"
    shutil.copy(ini_file, bak_file)

    new_file = ini_file + NEW_FILE_EXT
    step = get_bkout_step(opt)

    f_in = open(bak_file, 'r') 
    f_out = open(new_file, 'w') 

    first_port = True

    title = []

    for line in f_in.readlines():
        line.strip()
        if re.search("^#", line) is not None:
            # The current format is: # name lanes alias index speed
            # Where the ordering of the columns can vary
            if len(title) == 0:
                title = line.split()[1:]
                print title
            f_out.write(line)
            continue

        line = line.lstrip()

        line_port = line.split()[0]

        if line_port in get_bkout_ports(port, opt):
            oidx, olanes, name, oporti, fp_idx = get_info_in_ini(line, title)

            if get_is_bkout(opt) and len(olanes) == 1:
                print("Port %s Already breakout ..." % (port))
                print("Existing ...")
                f_in.close()
                f_out.close()
                shutil.copy(bak_file, new_file)

                sys.exit()

            #
            # Non-Breakout case
            #
            if not get_is_bkout(opt) and first_port:
                idx = oidx
                lanes = []
                for i in range(0, get_bkout_lanes(opt), 1):
                    lanes.append(str(int(olanes[0])+i))
                
                porti = oporti

            if get_is_bkout(opt):
                idx = oidx
                lanes = olanes
                porti = oporti

            #
            # original string:
            # Ethernet20      69,70,71,72           hundredGigE6
            #
            print("    %s" % line.rstrip())


            # Generate new interface line
            for i in range(0, len(lanes), step):
                #
                # Ethernet20
                #
                temp_str = "Ethernet%d" % (int(idx) + i)
                new_intf = "%-15s " % temp_str

                temp_str = lanes[i+0]
                #
                # generate  69
                #
                for j in range(1, step):
                    temp_str += ",%s" % (lanes[i+j])
                new_intf += "%-21s " % temp_str

                #
                # Generate twentyfiveGigE6:i
                #
                if get_is_bkout(opt):
                    temp_str = "%s%s:%d" % (get_bkout_subport_name(opt), porti, (i/step + 1))
                else:
                    temp_str = "%s%s" % (get_bkout_subport_name(opt), porti)

                new_intf += "%-19s " % temp_str

                #
                # index
                #
                if fp_idx is not None:
                    temp_str = "%d" % (fp_idx)
                    new_intf += "%-6s " % temp_str


                #
                # speed
                #
                temp_str = "%d000" % get_bkout_subport_speed(opt)
                new_intf += "%-10s " % temp_str

                #
                # valid_speeds
                #
                if 'valid_speeds' in title:
                    temp_str = get_bkout_subport_speed(opt)
                    if get_bkout_subport_speed(opt) == 100 or get_bkout_subport_speed(opt) == 40:
                        temp_str = "100000,40000"
                    if get_bkout_subport_speed(opt) == 25:
                        temp_str = "25000"
                    if get_bkout_subport_speed(opt) == 10:
                        temp_str = "10000"

                    new_intf += "%-10s " % temp_str


                if not get_is_bkout(opt) and first_port:
                    print "===>" + new_intf
                    new_intf += "\n"
                    f_out.write(new_intf)
                    first_port = False
                if get_is_bkout(opt):
                    print "===>" + new_intf
                    new_intf += "\n"
                    f_out.write(new_intf)

        else:
            f_out.write(line)

    print "--------------------------------------------------------"
    f_in.close()
    f_out.close()

    print lanes
    return lanes

# 
# Parse logic port, phyical port, speed from bcm 
#
def parse_port_bcm(bcm_str):
    lp = bcm_str.split("=")[0].split("_")[1]
    pp = bcm_str.split("=")[1].split(":")[0]
    sp = bcm_str.split("=")[1].split(":")[1]

    return lp, pp, sp
    
#
# portmap_84=81:100
# 
# portmap_84=81:25
# portmap_85=82:25
# portmap_86=83:25
# portmap_87=84:25
# 
#
def break_in_bcm(port, lanes, bcm_file, opt):
    print("Breaking %s to %s in bcm ..." % (port, opt))

    bak_file = bcm_file + ".bak"
    shutil.copy(bcm_file, bak_file)

    new_file = bcm_file + NEW_FILE_EXT
    step = get_bkout_step(opt)

    f_in = open(bak_file, 'r') 
    f_out = open(new_file, 'w') 

    first_port = True
    print lanes
    for oline in f_in.readlines():
        line = oline.lstrip()

        if line.startswith('#'):
            f_out.write(oline)
            continue

        if not line.startswith("portmap"):
            f_out.write(oline)
            continue

        ### logic port, phyical port, speed
        lp, pp, sp =  parse_port_bcm(line)
        if pp not in lanes:
            f_out.write(oline)
            continue

        #### generate new port map
        print("    %s" % line.rstrip())
        for i in range(0, len(lanes), step):
            new_intf = "portmap_%d=%d:%d" % ((int(lp) + i), (int(pp)+i), get_bkout_subport_speed(opt))

            if not get_is_bkout(opt) and first_port:
                f_out.write(new_intf)
                f_out.write("\n")
                print "===>" + new_intf
                first_port = False
            if get_is_bkout(opt):
                f_out.write(new_intf)
                f_out.write("\n")
                print "===>" + new_intf

    print "--------------------------------------------------------"
    f_in.close()
    f_out.close()

#
# breakout ports in json file
# 
def break_in_cfg(port, cfg_file, lanes, opt):
    step = get_bkout_step(opt)
    print("Breaking %s to %s in cfg ... " % (port, opt))

    bak_file = cfg_file + ".bak"
    shutil.copy(cfg_file, bak_file)

    new_file = cfg_file + NEW_FILE_EXT
 
    with open(bak_file) as f:
        data = json.load(f)

    with open(cfg_file, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

    ###
    ### Process in 'INTERFACE'
    ###
    if 'INTERFACE' in data:
        for key, value in sorted(data['INTERFACE'].iteritems()):
            pkey = key.split('|')[0]
            if port == pkey:
                data['INTERFACE'].pop(key)

    ###
    ### Process in 'PORT'


    ### remove port instance in data
    ###
    ports = get_bkout_ports(port, opt)
    for x in ports:
        if data['PORT'].get(x) != None:
            port_instance = data['PORT'].get(x)
            data['PORT'].pop(x)
            print "    ", x, port_instance

    idx = port.split()[0].split(INTERFACE_KEY,1)[1]
    porti = re.sub('.*?([0-9]*)$',r'\1', port_instance['alias'].split(":")[0])

    for i in range(0, len(lanes), step):

        if get_is_bkout(opt):
            port_instance['lanes'] = lanes[i]
            port_instance['alias'] = get_bkout_subport_name(opt) + porti + ':' + str(i/step + 1)
        else:
            port_instance['alias'] = get_bkout_subport_name(opt) + porti
            port_instance['lanes'] = ','.join(str(e) for e in lanes)

        port_instance['speed'] = str(get_bkout_subport_speed(opt)) + "000"

        new_port = INTERFACE_KEY + str(int(idx) +i)
        xxx = copy.deepcopy(port_instance)
        data['PORT'][new_port] = xxx
        ### print data['PORT'][new_port]

    for i in range(0, len(lanes), step):
        new_port = INTERFACE_KEY + str(int(idx) +i)
        print "===>", new_port, data['PORT'][new_port]

    with open(new_file, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

    print "--------------------------------------------------------"

def break_a_port(port, opt, platform, hwsku):
    if not SIM_HOST:
        ini_file = get_ini_file(platform, hwsku)
        bcm_file = get_bcm_file(platform, hwsku)
        cfg_file = get_cfg_file(platform, hwsku)
    else:
        ini_file = "port_config.ini"
        bcm_file = "config.bcm"
        cfg_file = "config_db.json"


    lanes = break_in_ini(port, ini_file, opt)
    break_in_bcm(port, lanes, bcm_file, opt)
    break_in_cfg(port, cfg_file, lanes, opt)

def usage():
    print "Usage: " + sys.argv[0] + " interface 4x100|4x25"
    print "Breakout None-breaokout a port"
    print "Options:"
    print "  -p port"
    print "  -o breakout option"
    for k in bko_dict:
        print "         %s" % k
    print "   "
    print "Example:"
    print "  Breakout port Ethernet4 to 4x10G"
    print "    %s -p Ethernet4 -o 4x10" % (sys.argv[0])
    print "  None-Breakout port Ethernet4 to 40G"
    print "    %s -p Ethernet4 -o 1x40" % (sys.argv[0])
    print "   "
    print "Note:"
    print "  Make sure understand which ports are able to breakout before execute command."
    print "  Make backup below config files"
    print "  - /usr/share/sonic/device/[platform]/[hwsku]/[config.bcm]"
    print "  - /usr/share/sonic/device/[platform]/[hwsku]/port_config.ini"
    print "  - /etc/sonic/config_db.json"

    sys.exit(1)

#
# check breakout option valid
#       configure files existing
#
def check_vaildation(platform, hwsku, port, opt):

    if not SIM_HOST:
        ini_file = get_ini_file(platform, hwsku)
    else:
        ini_file = "port_config.ini"

    ports =  get_bkout_ports(port, opt)
    if ports == None:
        print("Wrong interface name:%s" % (port))
        return False

    ### need re-visit
    idx   = port.split()[0].split(INTERFACE_KEY,1)[1]
    
    if  int(idx) % get_bkout_lanes(opt) != 0:
        print("Can not work on port:%s" % (port))
        return False
    
    f_in = open(ini_file, 'r') 

    ini_ports = []
    ini_lanes = []
    port_found = 0
    title = []

    for line in f_in.readlines():
        line = line.lstrip()
        line.strip()
        if re.search("^#", line) is not None:
            # The current format is: # name lanes alias index speed
            # Where the ordering of the columns can vary
            title = line.split()[1:]
            continue


        line_port = line.split()[0]

        ### Check breakout case
        if get_is_bkout(opt):
            if line_port == port:
                port_found += 1
                oidx, olanes, name, oporti, fp_idx = get_info_in_ini(line, title)
                if len(olanes) != get_bkout_lanes(opt):
                    print("port %s can not breakout to %s." % (port, opt))
                    f_in.close()
                    return False
        else:
            if line_port in ports:
                port_found += 1
                oidx, olanes, name, oporti, fp_idx = get_info_in_ini(line, title)
                ini_ports.append(line_port)
                ini_lanes += olanes

    f_in.close()

    if get_is_bkout(opt) and port_found != 1:
        if port_found == 0:
            print("port %s does not exist." % (port))
        if port_found > 1:
            print("Duplicate(%d) port %s found in INI file." % (port_found, port))
        return False

    if not get_is_bkout(opt):
        if len(ini_lanes) != get_bkout_lanes(opt):
            print("Port %s can not non-breakout." % (port))
            return False
        if len(ini_lanes) == 0:
            print("port %s does not exist." % (port))
            return False

        ### need re-visit for 2x50 case, etc
        if port_found != get_bkout_lanes(opt):
            print("Port %s can not non-breakout." % (port))
            return False

    return True


def process_args(argv):
    verbose = 0
    pde = 0
    port = None
    opt = None

    try:
        opts, args = getopt.getopt(argv, "hvdp:o:", \
        ["help", "verbose", "pde", "port=", "opt="])

        for opt,arg in opts:
            if opt in ('-h','--help'):
                usage()
                return
            if opt in ('-v', '--verbose'):
                verbose = 1
            if opt in ('-p', '--port'):
                port = arg
            if opt in ('-o', '--option'):
                opt = arg
            if opt in ('-d', '--pde'):
                pde = 1
    except getopt.GetoptError:
        print("Error: Invalid option")
        sys.exit(1)

    if port == None or opt == None:
        print "Error: must give -p [port] and -o [option]"

        usage()
        sys.exit(1)

    return verbose, port, opt, pde
        
### Breakout interface 
def main(argv):

    if len(argv) > 0 and argv[0] == "-h":
        usage()
        return

    verbose, port, opt, pde = process_args(argv)
    """
    print verbose, port, opt
    """

    if not bko_opt_valid(opt):
        print("Invalid breakout option :%s" % (opt))
        return

    if not SIM_HOST:
        platform = get_platform()
        if pde == 1:
            hwsku = get_pde_hwsku(platform)
        else:
            hwsku = get_hwsku()
    else:
        platform = 'xxx'
        hwsku = 'yyy'

    """
    print("Platform=[%s]" % (platform))
    print("hwsku=[%s]" % (hwsku))
    display_files(platform, hwsku)
    """

    if check_vaildation(platform, hwsku, port, opt) == False:
        print("breakout options checking failed.")
        return

    break_a_port(port, opt, platform, hwsku)


if __name__ == "__main__":
    main(sys.argv[1:])

