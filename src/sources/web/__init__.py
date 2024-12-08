import ipaddress
import urllib.request

from sources import SourceResult


async def fetch_ip(config, verbose=False):
    public_ip = urllib.request.urlopen(config["url"]).read().decode('utf8')
    try:
        return SourceResult(True, [str(ipaddress.ip_address(public_ip))])
    except ValueError:
        print(f"Web: Unable to contact: {public_ip}")
        return SourceResult(False, [])
