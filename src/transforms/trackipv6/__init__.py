import ipaddress


async def transform_ips(config, ipRecord, verbose=False):
    if config["trackSource"] not in ipRecord:
        raise ValueError("TrackIPv6: Tracked IP source does not exist: " +
                         config["trackSource"])
    if config["ipSource"] not in ipRecord:
        raise ValueError(
            "TrackIPv6: IP source does not exist: " + config["ipSource"])
    if len(ipRecord[config["trackSource"]]) == 0:
        raise ValueError("TrackIPv6: Tracked IP source is empty: " +
                         config["trackSource"])
    trackIp = ipaddress.ip_address(ipRecord[config["trackSource"]][0])
    prefixLength = int(config["trackPrefixLength"])
    if prefixLength < 0 or prefixLength > 128:
        raise ValueError("TrackIPv6: Invalid prefix length: " +
                         prefixLength)
    # Set suffix of IP to zeroes
    prefix = int.from_bytes(
        trackIp.packed, 'big') >> (128 - prefixLength) << (128 - prefixLength)
    translatedIps = []
    for ip in ipRecord[config["ipSource"]]:
        # Set first {prefixLength} bits from IP to zeroes
        suffix = int.from_bytes(
            ipaddress.ip_address(ip).packed, 'big') & ~((2**128)-(2**(128 - prefixLength)))
        # Combine prefix and suffix
        translatedIp = ipaddress.ip_address(
            (prefix | suffix).to_bytes(16, 'big'))
        translatedIps.append(str(translatedIp))
    return translatedIps
