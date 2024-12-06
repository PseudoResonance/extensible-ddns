import ipaddress


async def fetch_ip(config):
    ips = []
    if "ips" in config:
        ips = config["ips"]
    if "ip" in config:
        ips.append(config["ip"])
    else:
        raise ValueError("Static: Config missing ips field")
    ipsFiltered = []
    for entry in ips:
        try:
            ipsFiltered.append(
                str(ipaddress.ip_address(entry)))
        except ValueError:
            print("Static: Invalid IP: " + entry)
    return ipsFiltered
