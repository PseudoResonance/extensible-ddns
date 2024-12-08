import ipaddress
import traceback
import dns.resolver

from sources import SourceResult


async def fetch_ip(config, verbose=False):
    try:
        queryResult = dns.resolver.resolve_at(
            config["dnsServer"], config["domain"], config["ipType"]
        )
        queryResult.response
        results = []
        for rr in queryResult:
            try:
                results.append(
                    str(ipaddress.ip_address(rr.address)))
            except ValueError:
                print(f"DNS: Invalid IP: {rr.address}")
        return SourceResult(True, results)
    except Exception:
        print(f"DNS: Unable to fetch records from: {config["dnsServer"]}")
        print(traceback.format_exc())
        return SourceResult(False, [])
