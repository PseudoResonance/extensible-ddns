import ipaddress


async def transform_ips(config, ipRecord, verbose=False) -> None:
    if config["trackSource"] not in ipRecord:
        raise ValueError("TrackIPv6: Tracked IP source does not exist: " +
                         config["trackSource"])
    if config["ipSource"] not in ipRecord:
        raise ValueError(
            "TrackIPv6: IP source does not exist: " + config["ipSource"])
    try:
        ipSuffix = ipaddress.ip_address(config["trackIpSuffix"])
    except ValueError:
        raise ValueError("TrackIPv6: Track IP Suffix is invalid: " +
                         config["trackIpSuffix"])
    groups = str(ipSuffix)[1:].count(":")
    suffix = ipSuffix.exploded[groups * -5:]
    trackIp = None
    for ip in ipRecord[config["trackSource"]]:
        ipAddr = ipaddress.ip_address(ip)
        if ipAddr.exploded.endswith(suffix):
            trackIp = ipAddr
            break
    if trackIp is None:
        raise ValueError("TrackIPv6: Unable to find IP with suffix: " +
                         config["trackIpSuffix"])
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
        translatedIps.append(translatedIp.compressed)
    return translatedIps
