#!/bin/bash

mkdir -p /etc/swss/teamd

sonic-cfggen -m /etc/sonic/minigraph.xml --var-json minigraph_portchannel_interfaces >/etc/swss/teamd/portchannel.json

mkdir -p /etc/teamd

python << END

import json
import os
with open('/etc/swss/teamd/portchannel.json') as json_file:    
    data = json.load(json_file)

for item in data:
    command = 'sonic-cfggen -a \'' + json.dumps(item) + '\' -t teamd.j2 >/etc/teamd/' + item['name']+ '.conf'
    os.system(command)

END

