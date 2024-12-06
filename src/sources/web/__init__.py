import ipaddress
import urllib.request


async def fetch_ip(config):
    public_ip = urllib.request.urlopen(config["url"]).read().decode('utf8')
    try:
        return [str(ipaddress.ip_address(public_ip))]
    except ValueError:
        print("Web: Invalid IP: " + public_ip)
