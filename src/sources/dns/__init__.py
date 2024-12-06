import ipaddress
import dns.resolver


async def fetch_ip(config):
    queryResult = dns.resolver.resolve_at(
        config["dnsServer"], config["domain"], config["ipType"]
    )
    results = []
    for rr in queryResult:
        try:
            results.append(
                str(ipaddress.ip_address(rr.address)))
        except ValueError:
            print("DNS: Invalid IP: " + rr.address)
    return results
