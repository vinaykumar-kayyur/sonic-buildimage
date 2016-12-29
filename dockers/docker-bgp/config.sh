#!/bin/bash

cd /etc/swss

awk '{system("python render_config.py -m /etc/swss/minigraph.xml "$1 ">"$2" && chown "$3" "$2" && chmod "$4" "$2)}' template_list 

