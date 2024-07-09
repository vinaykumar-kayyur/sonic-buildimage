use clap::Parser;
use pnet::datalink::Channel::Ethernet;
use pnet::datalink::{self, DataLinkSender, MacAddr, NetworkInterface};
use std::fs::read_to_string;
use std::result::Result;
use std::str::FromStr;
use std::thread;
use std::time::Duration;

const BROADCAST_MAC: [u8; 6] = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff];

#[derive(Debug)]
pub struct WolErr {
    pub msg: String,
    pub code: i32,
}

impl std::error::Error for WolErr {}

impl std::fmt::Display for WolErr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Error: {}", self.msg)
    }
}

enum WolErrCode {
    SocketError = 1,
    InvalidArguments = 2,
    UnknownError = 999,
}

pub fn build_and_send() -> Result<(), WolErr> {
    let args = WolArgs::parse();
    let target_macs = parse_target_macs(&args)?;
    valide_arguments(&args)?;
    let src_mac = get_interface_mac(&args.interface)?;
    let mut tx = open_tx_channel(&args.interface)?;
    for target_mac in target_macs {
        if args.verbose {
            println!(
                "Building and sending packet to target mac address {}",
                target_mac
                    .iter()
                    .map(|b| format!("{:02X}", b))
                    .collect::<Vec<String>>()
                    .join(":")
            );
        }
        let dst_mac = if args.broadcast {
            BROADCAST_MAC
        } else {
            target_mac
        };
        let magic_bytes = build_magic_packet(&src_mac, &dst_mac, &target_mac, &args.password)?;
        send_magic_packet(
            &mut tx,
            magic_bytes,
            &args.count,
            &args.interval,
            &args.verbose,
        )?;
    }

    Ok(())
}

fn valide_arguments(args: &WolArgs) -> Result<(), WolErr> {
    if !is_operstate_up(&args.interface)? {
        return Err(WolErr {
            msg: format!(
                "Invalid value for \"INTERFACE\": interface {} is not up",
                args.interface
            ),
            code: WolErrCode::InvalidArguments as i32,
        });
    }
    Ok(())
}

fn parse_mac_addr(mac_str: &str) -> Result<[u8; 6], WolErr> {
    MacAddr::from_str(mac_str)
        .map(|mac| mac.octets())
        .map_err(|_| WolErr {
            msg: String::from("Invalid MAC address"),
            code: WolErrCode::InvalidArguments as i32,
        })
}

fn parse_ipv4_addr(ipv4_str: &str) -> Result<Vec<u8>, WolErr> {
    if !is_ipv4_address_valid(ipv4_str) {
        Err(WolErr {
            msg: String::from("Invalid IPv4 address"),
            code: WolErrCode::InvalidArguments as i32,
        })
    } else {
        ipv4_str
            .split('.')
            .map(|octet| octet.parse::<u8>())
            .collect::<Result<Vec<u8>, _>>()
            .map_err(|_| WolErr {
                msg: String::from("Invalid IPv4 address"),
                code: WolErrCode::InvalidArguments as i32,
            })
    }
}

fn parse_password(password: &str) -> Result<Password, WolErr> {
    if is_ipv4_address_valid(password) {
        Ok(Password(parse_ipv4_addr(password)?))
    } else if is_mac_string_valid(password) {
        parse_mac_addr(password).map(|mac| Password(mac.to_vec()))
    } else {
        Err(WolErr {
            msg: String::from("Invalid password"),
            code: WolErrCode::InvalidArguments as i32,
        })
    }
}

fn parse_target_macs(args: &WolArgs) -> Result<Vec<[u8; 6]>, WolErr> {
    let target_macs: Vec<&str> = args.target_mac.split(',').collect();
    let mut macs = Vec::new();
    for mac_str in target_macs {
        macs.push(parse_mac_addr(mac_str)?);
    }
    Ok(macs)
}

fn is_operstate_up(interface: &str) -> Result<bool, WolErr> {
    let state_file_path = format!("/sys/class/net/{}/operstate", interface);
    match read_to_string(state_file_path) {
        Ok(content) => Ok(content.trim() == "up"),
        Err(_) => Err(WolErr {
            msg: format!(
                "Invalid value for \"INTERFACE\": invalid SONiC interface name {}",
                interface
            ),
            code: WolErrCode::InvalidArguments as i32,
        }),
    }
}

fn is_mac_string_valid(mac_str: &str) -> bool {
    let mac_str = mac_str.replace(':', "");
    mac_str.len() == 12 && mac_str.chars().all(|c| c.is_ascii_hexdigit())
}

fn is_ipv4_address_valid(ipv4_str: &str) -> bool {
    ipv4_str.split('.').count() == 4
        && ipv4_str
            .split('.')
            .all(|octet| octet.parse::<u64>().map_or(false, |n| n < 256))
}

fn get_interface_mac(interface_name: &String) -> Result<[u8; 6], WolErr> {
    if let Some(interface) = datalink::interfaces()
        .into_iter()
        .find(|iface: &NetworkInterface| iface.name == *interface_name)
    {
        if let Some(mac) = interface.mac {
            Ok(mac.octets())
        } else {
            Err(WolErr {
                msg: String::from("Could not get MAC address of target interface"),
                code: WolErrCode::UnknownError as i32,
            })
        }
    } else {
        Err(WolErr {
            msg: String::from("Could not find target interface"),
            code: WolErrCode::InvalidArguments as i32,
        })
    }
}

fn build_magic_packet(
    src_mac: &[u8; 6],
    dst_mac: &[u8; 6],
    target_mac: &[u8; 6],
    password: &Option<Password>,
) -> Result<Vec<u8>, WolErr> {
    let password_len = password.as_ref().map_or(0, |p| p.ref_bytes().len());
    let mut pkt = vec![0u8; 116 + password_len];
    pkt[0..6].copy_from_slice(dst_mac);
    pkt[6..12].copy_from_slice(src_mac);
    pkt[12..14].copy_from_slice(&[0x08, 0x42]);
    pkt[14..20].copy_from_slice(&[0xff; 6]);
    pkt[20..116].copy_from_slice(&target_mac.repeat(16));
    if let Some(p) = password {
        pkt[116..116 + password_len].copy_from_slice(p.ref_bytes());
    }
    Ok(pkt)
}

fn send_magic_packet(
    tx: &mut Box<dyn DataLinkSender>,
    packet: Vec<u8>,
    count: &u8,
    interval: &u64,
    verbose: &bool,
) -> Result<(), WolErr> {
    for nth in 0..*count {
        match tx.send_to(&packet, None) {
            Some(Ok(_)) => {}
            Some(Err(e)) => {
                return Err(WolErr {
                    msg: format!("Network is down: {}", e),
                    code: WolErrCode::SocketError as i32,
                });
            }
            None => {
                return Err(WolErr {
                    msg: String::from("Network is down"),
                    code: WolErrCode::SocketError as i32,
                });
            }
        }
        if *verbose {
            println!(
                "  | -> Sent the {}th packet and sleep for {} seconds",
                &nth + 1,
                &interval
            );
            println!(
                "    | -> Packet bytes in hex {}",
                &packet
                    .iter()
                    .fold(String::new(), |acc, b| acc + &format!("{:02X}", b))
            )
        }
        thread::sleep(Duration::from_millis(*interval));
    }
    Ok(())
}

fn open_tx_channel(interface: &str) -> Result<Box<dyn DataLinkSender>, WolErr> {
    if let Some(interface) = datalink::interfaces()
        .into_iter()
        .find(|iface: &NetworkInterface| iface.name == interface)
    {
        match datalink::channel(&interface, Default::default()) {
            Ok(Ethernet(tx, _)) => Ok(tx),
            Ok(_) => Err(WolErr {
                msg: String::from("Network is down"),
                code: WolErrCode::SocketError as i32,
            }),
            Err(e) => Err(WolErr {
                msg: format!("Network is down: {}", e),
                code: WolErrCode::SocketError as i32,
            }),
        }
    } else {
        Err(WolErr {
            msg: format!(
                "Invalid value for \"INTERFACE\": interface {} is not up",
                interface
            ),
            code: WolErrCode::InvalidArguments as i32,
        })
    }
}

#[derive(Parser, Debug)]
#[command(
    next_line_help = true,
    about = "
This tool can generate and send wake on LAN magic packets with target interface and mac

Examples:
    wol Ethernet10 00:11:22:33:44:55
    wol Ethernet10 00:11:22:33:44:55 -b
    wol Vlan1000 00:11:22:33:44:55,11:33:55:77:99:bb -p 00:22:44:66:88:aa
    wol Vlan1000 00:11:22:33:44:55,11:33:55:77:99:bb -p 192.168.1.1 -c 3 -i 2000"
)]
struct WolArgs {
    /// The name of the network interface to send the magic packet through
    interface: String,

    /// The MAC address of the target device, formatted as a colon-separated string (e.g. "00:11:22:33:44:55")
    target_mac: String,

    /// The flag to indicate if use broadcast MAC address instead of target device's MAC address as Destination MAC Address in Ethernet Frame Header [default: false]
    #[arg(short, long, default_value_t = false)]
    broadcast: bool,

    /// An optional 4 or 6 byte password, in ethernet hex format or quad-dotted decimal (e.g. "127.0.0.1" or "00:11:22:33:44:55")
    #[arg(short, long, value_parser = parse_password)]
    password: Option<Password>,

    /// The number of times to send the magic packet [default: 1][range: 1-5]
    #[arg(short, long, default_value_t = 1, value_parser = clap::value_parser!(u8).range(1..=5))]
    count: u8,

    /// The interval in milliseconds between each magic packet transmission [default: 0][range: 0-2000]
    #[arg(short, long, default_value_t = 0, value_parser = clap::value_parser!(u64).range(0..=2000))]
    interval: u64,

    /// The flag to indicate if we should print verbose output
    #[arg(short, long)]
    verbose: bool,
}

#[derive(Debug, Clone)]
struct Password(Vec<u8>);

impl Password {
    fn ref_bytes(&self) -> &Vec<u8> {
        &self.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_mac_addr() {
        let mac_str = "00:11:22:33:44:55";
        let mac = parse_mac_addr(mac_str).unwrap();
        assert_eq!(mac, [0x00, 0x11, 0x22, 0x33, 0x44, 0x55]);

        let mac_str = "00:11:22:33:44:GG";
        assert!(parse_mac_addr(mac_str).is_err());
        assert_eq!(
            parse_mac_addr(mac_str).unwrap_err().msg,
            "Invalid MAC address"
        );
        assert_eq!(
            parse_mac_addr(mac_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );

        let mac_str = "00-01-22-33-44-55";
        assert!(parse_mac_addr(mac_str).is_err());
        assert_eq!(
            parse_mac_addr(mac_str).unwrap_err().msg,
            "Invalid MAC address"
        );
        assert_eq!(
            parse_mac_addr(mac_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );
    }

    #[test]
    fn test_parse_ipv4_addr() {
        let ipv4_str = "127.0.0.1";
        let ipv4 = parse_ipv4_addr(ipv4_str).unwrap();
        assert_eq!(ipv4, [127, 0, 0, 1]);

        let ipv4_str = "127.0.0.256";
        assert!(parse_ipv4_addr(ipv4_str).is_err());
        assert_eq!(
            parse_ipv4_addr(ipv4_str).unwrap_err().msg,
            "Invalid IPv4 address"
        );
        assert_eq!(
            parse_ipv4_addr(ipv4_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );

        let ipv4_str = "127.0.0";
        assert!(parse_ipv4_addr(ipv4_str).is_err());
        assert_eq!(
            parse_ipv4_addr(ipv4_str).unwrap_err().msg,
            "Invalid IPv4 address"
        );
        assert_eq!(
            parse_ipv4_addr(ipv4_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );

        let ipv4_str = "::1";
        assert!(parse_ipv4_addr(ipv4_str).is_err());
        assert_eq!(
            parse_ipv4_addr(ipv4_str).unwrap_err().msg,
            "Invalid IPv4 address"
        );
        assert_eq!(
            parse_ipv4_addr(ipv4_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );
    }

    #[test]
    fn test_parse_password() {
        let password_str = "127.0.0.1";
        let password = parse_password(password_str);
        assert_eq!(*password.unwrap().ref_bytes(), [127, 0, 0, 1]);

        let password_str = "00:11:22:33:44:55";
        let password = parse_password(password_str);
        assert_eq!(*password.unwrap().ref_bytes(), [0, 17, 34, 51, 68, 85]);

        let password_str = "127.0.0.256";
        assert!(parse_password(password_str).is_err());
        assert_eq!(
            parse_password(password_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );

        let password_str = "127.0.0";
        assert!(parse_password(password_str).is_err());
        assert_eq!(
            parse_password(password_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );

        let password_str = "::1";
        assert!(parse_password(password_str).is_err());
        assert_eq!(
            parse_password(password_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );

        let password_str = "00:11:22:33:44:GG";
        assert!(parse_password(password_str).is_err());
        assert_eq!(
            parse_password(password_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );

        let password_str = "00-01-22-33-44-55";
        assert!(parse_password(password_str).is_err());
        assert_eq!(
            parse_password(password_str).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );
    }

    #[test]
    fn test_parse_target_macs() {
        let mut args = WolArgs {
            interface: "Ethernet10".to_string(),
            target_mac: "00:11:22:33:44:55".to_string(),
            broadcast: false,
            password: None,
            count: 1,
            interval: 0,
            verbose: false,
        };
        let target_macs = parse_target_macs(&args).unwrap();
        assert_eq!(target_macs.len(), 1);
        assert_eq!(target_macs[0], [0x00, 0x11, 0x22, 0x33, 0x44, 0x55]);

        args.target_mac = "00:11:22:33:44:55,11:22:33:44:55:66,22:33:44:55:66:77".to_string();
        let target_macs = parse_target_macs(&args).unwrap();
        assert_eq!(target_macs.len(), 3);
        assert_eq!(target_macs[0], [0x00, 0x11, 0x22, 0x33, 0x44, 0x55]);
        assert_eq!(target_macs[1], [0x11, 0x22, 0x33, 0x44, 0x55, 0x66]);
        assert_eq!(target_macs[2], [0x22, 0x33, 0x44, 0x55, 0x66, 0x77]);

        args.target_mac = "00:01".to_string();
        assert!(parse_target_macs(&args).is_err());
        assert_eq!(
            parse_target_macs(&args).unwrap_err().msg,
            "Invalid MAC address"
        );
        assert_eq!(
            parse_target_macs(&args).unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );
    }

    #[test]
    fn test_is_mac_string_valid() {
        assert!(is_mac_string_valid("00:11:22:33:44:55"));
        assert!(!is_mac_string_valid(""));
        assert!(!is_mac_string_valid("0:1:2:3:4:G"));
        assert!(!is_mac_string_valid("00:11:22:33:44:GG"));
        assert!(!is_mac_string_valid("00-11-22-33-44-55"));
        assert!(!is_mac_string_valid("00:11:22:33:44:55:66"));
    }

    #[test]
    fn test_is_ipv4_address_valid() {
        assert!(is_ipv4_address_valid("192.168.1.1"));
        assert!(!is_ipv4_address_valid(""));
        assert!(!is_ipv4_address_valid("0::1"));
        assert!(!is_ipv4_address_valid("192.168.1"));
        assert!(!is_ipv4_address_valid("192.168.1.256"));
        assert!(!is_ipv4_address_valid("192.168.1.1.1"));
    }

    #[test]
    fn test_build_magic_packet() {
        let src_mac = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55];
        let target_mac = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff];
        let four_bytes_password = Some(Password(vec![0x00, 0x11, 0x22, 0x33]));
        let magic_packet =
            build_magic_packet(&src_mac, &target_mac, &target_mac, &four_bytes_password).unwrap();
        assert_eq!(magic_packet.len(), 120);
        assert_eq!(&magic_packet[0..6], &target_mac);
        assert_eq!(&magic_packet[6..12], &src_mac);
        assert_eq!(&magic_packet[12..14], &[0x08, 0x42]);
        assert_eq!(&magic_packet[14..20], &[0xff; 6]);
        assert_eq!(&magic_packet[20..116], target_mac.repeat(16));
        assert_eq!(&magic_packet[116..120], &[0x00, 0x11, 0x22, 0x33]);
        let six_bytes_password = Some(Password(vec![0x00, 0x11, 0x22, 0x33, 0x44, 0x55]));
        let magic_packet =
            build_magic_packet(&src_mac, &target_mac, &target_mac, &six_bytes_password).unwrap();
        assert_eq!(magic_packet.len(), 122);
        assert_eq!(&magic_packet[0..6], &target_mac);
        assert_eq!(&magic_packet[6..12], &src_mac);
        assert_eq!(&magic_packet[12..14], &[0x08, 0x42]);
        assert_eq!(&magic_packet[14..20], &[0xff; 6]);
        assert_eq!(&magic_packet[20..116], target_mac.repeat(16));
        assert_eq!(
            &magic_packet[116..122],
            &[0x00, 0x11, 0x22, 0x33, 0x44, 0x55]
        );
    }

    #[test]
    fn test_build_magic_packet_without_password() {
        let src_mac = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55];
        let dst_mac = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff];
        let target_mac = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06];
        let magic_packet = build_magic_packet(&src_mac, &dst_mac, &target_mac, &None).unwrap();
        assert_eq!(magic_packet.len(), 116);
        assert_eq!(&magic_packet[0..6], &dst_mac);
        assert_eq!(&magic_packet[6..12], &src_mac);
        assert_eq!(&magic_packet[12..14], &[0x08, 0x42]);
        assert_eq!(&magic_packet[14..20], &[0xff; 6]);
        assert_eq!(&magic_packet[20..116], target_mac.repeat(16));
    }

    #[test]
    fn verify_args_parse() {
        // Interface and target mac are required
        let result = WolArgs::try_parse_from(&["wol", "eth0", "00:11:22:33:44:55"]);
        assert!(result.as_ref().is_ok_and(|a| a.interface == "eth0"));
        assert!(result.is_ok_and(|a| a.target_mac == "00:11:22:33:44:55"));
        let result = WolArgs::try_parse_from(&["wol"]);
        assert!(result.is_err());
        assert_eq!(
            result.unwrap_err().to_string(),
            "error: the following required arguments were not provided:\n  <INTERFACE>\n  <TARGET_MAC>\n\nUsage: wol <INTERFACE> <TARGET_MAC>\n\nFor more information, try '--help'.\n"
        );
        // Mac address should valid
        let args =
            WolArgs::try_parse_from(&["wol", "Ethernet10", "00:11:22:33:44:55,00:01:02:03:04:05"])
                .unwrap();
        let macs = parse_target_macs(&args).unwrap();
        assert_eq!(macs.len(), 2);
        assert_eq!(macs[0], [0x00, 0x11, 0x22, 0x33, 0x44, 0x55]);
        assert_eq!(macs[1], [0x00, 0x01, 0x02, 0x03, 0x04, 0x05]);
        let args = WolArgs::try_parse_from(&["wol", "Ethernet10", "00:11:22:33:44:GG"]).unwrap();
        let result: Result<Vec<[u8; 6]>, WolErr> = parse_target_macs(&args);
        assert!(result.is_err());
        assert_eq!(result.as_ref().unwrap_err().msg, "Invalid MAC address");
        assert_eq!(
            result.unwrap_err().code,
            WolErrCode::InvalidArguments as i32
        );
        // Password can be set
        let args = WolArgs::try_parse_from(&[
            "wol",
            "eth0",
            "00:01:02:03:04:05",
            "-b",
            "-p",
            "192.168.0.0",
        ])
        .unwrap();
        assert_eq!(args.password.unwrap().ref_bytes(), &[192, 168, 0, 0]);
        let args = WolArgs::try_parse_from(&[
            "wol",
            "eth0",
            "00:01:02:03:04:05",
            "-b",
            "-p",
            "00:01:02:03:04:05",
        ])
        .unwrap();
        assert_eq!(args.password.unwrap().ref_bytes(), &[0, 1, 2, 3, 4, 5]);
        let result = WolArgs::try_parse_from(&["wol", "eth0", "-b", "-p", "xxx"]);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err().to_string(), "error: invalid value 'xxx' for '--password <PASSWORD>': Error: Invalid password\n\nFor more information, try '--help'.\n");
        // Count should be between 1 and 5
        let args = WolArgs::try_parse_from(&["wol", "eth0", "00:01:02:03:04:05", "-b"]).unwrap();
        assert_eq!(args.count, 1); // default value
        let args = WolArgs::try_parse_from(&["wol", "eth0", "00:01:02:03:04:05", "-b", "-c", "5"])
            .unwrap();
        assert_eq!(args.count, 5);
        let result =
            WolArgs::try_parse_from(&["wol", "eth0", "00:01:02:03:04:05", "-b", "-c", "0"]);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err().to_string(), "error: invalid value '0' for '--count <COUNT>': 0 is not in 1..=5\n\nFor more information, try '--help'.\n");
        // Interval should be between 0 and 2000
        let args = WolArgs::try_parse_from(&["wol", "eth0", "00:01:02:03:04:05", "-b"]).unwrap();
        assert_eq!(args.interval, 0); // default value
        let args =
            WolArgs::try_parse_from(&["wol", "eth0", "00:01:02:03:04:05", "-b", "-i", "2000"])
                .unwrap();
        assert_eq!(args.interval, 2000);
        let result =
            WolArgs::try_parse_from(&["wol", "eth0", "00:01:02:03:04:05", "-b", "-i", "2001"]);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err().to_string(), "error: invalid value '2001' for '--interval <INTERVAL>': 2001 is not in 0..=2000\n\nFor more information, try '--help'.\n");
        // Verbose can be set
        let args =
            WolArgs::try_parse_from(&["wol", "eth0", "00:01:02:03:04:05", "-b", "--verbose"])
                .unwrap();
        assert_eq!(args.verbose, true);
    }
}
