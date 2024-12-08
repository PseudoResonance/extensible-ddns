import ipaddress

from sources import SourceResult


async def fetch_ip(config, verbose=False):
    ips = []
    if "ips" in config:
        ips = config["ips"]
    if "ip" in config:
        ips.append(config["ip"])
    if len(ips) == 0:
        print("Static: Config missing ips field")
        return SourceResult(False, [])
    ipsFiltered = []
    for entry in ips:
        try:
            ipsFiltered.append(
                str(ipaddress.ip_address(entry)))
        except ValueError:
            print(f"Static: Invalid IP: {entry}")
    return SourceResult(True, ipsFiltered)
