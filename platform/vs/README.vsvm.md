HOWTO Use Virtual Switch (VM)

1. Install libvirt, kvm, qemu

```
sudo apt-get install libvirt-clients qemu-kvm libvirt-bin
```

2. Create SONiC VM

```
$ sudo virsh
Welcome to virsh, the virtualization interactive terminal.

Type:  'help' for help with commands
       'quit' to quit

virsh # 
virsh # create sonic.xml
Domain sonic created from sonic.xml

virsh # 
```

3. Access virtual switch:

    1. Connect SONiC VM via console
    ```
    $ telnet 127.0.0.1 7000
    ```
    
    OR

    2. Connect SONiC VM via SSH
        
        1. Connect via console (see 3.1 above)

        2. Request a new DHCP address
        ```
        sudo dhclient -v
        ```
        
        3. Connect via SSH
        ```
        $ ssh -p 3040 admin@127.0.0.1
        ```
