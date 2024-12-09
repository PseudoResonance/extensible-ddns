import ipaddress

from sources import SourceResult

IPV6_BIT_LENGTH = 128


async def transform_ips(config, ipRecord: dict[str, SourceResult], verbose=False):
    if config["trackSource"] not in ipRecord:
        print(f"TrackIPv6: Tracked IP source does not exist: {
              config["trackSource"]}")
        return SourceResult(False, [])
    if not ipRecord[config["trackSource"]].status:
        print(f"TrackIPv6: Tracked IP source failed to run: {
              config["trackSource"]}")
        return SourceResult(False, [])
    if config["ipSource"] not in ipRecord:
        print(f"TrackIPv6: IP source does not exist: {config["ipSource"]}")
        return SourceResult(False, [])
    if not ipRecord[config["ipSource"]].status:
        print(f"TrackIPv6: IP source failed to run: {config["ipSource"]}")
        return SourceResult(False, [])
    if len(ipRecord[config["trackSource"]].ips) == 0:
        print(f"TrackIPv6: Tracked IP source is empty: {
              config["trackSource"]}")
        return SourceResult(False, [])
    trackIp = ipaddress.ip_address(ipRecord[config["trackSource"]].ips[0])
    prefixLength = int(config["trackPrefixLength"])
    if prefixLength < 0 or prefixLength > IPV6_BIT_LENGTH:
        print(f"TrackIPv6: Invalid prefix length: {prefixLength}")
        return SourceResult(False, [])
    # Set suffix of IP to zeroes
    prefix = int.from_bytes(
        trackIp.packed, 'big') >> (IPV6_BIT_LENGTH - prefixLength) << (IPV6_BIT_LENGTH - prefixLength)
    translatedIps = []
    for ip in ipRecord[config["ipSource"]].ips:
        # Set first {prefixLength} bits from IP to zeroes
        suffix = int.from_bytes(
            ipaddress.ip_address(ip).packed, 'big') & ~((2**IPV6_BIT_LENGTH)-(2**(IPV6_BIT_LENGTH - prefixLength)))
        # Combine prefix and suffix
        translatedIp = ipaddress.ip_address(
            (prefix | suffix).to_bytes(int(IPV6_BIT_LENGTH / 8), 'big'))
        translatedIps.append(str(translatedIp))
    return SourceResult(True, translatedIps)
