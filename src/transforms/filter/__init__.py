import ipaddress


async def transform_ips(config, ipRecord, verbose=False):
    if config["source"] not in ipRecord:
        raise ValueError("Filter: IP source does not exist: " +
                         config["source"])
    match config["filterMethod"].lower():
        case "suffix":
            try:
                ipSuffix = ipaddress.ip_address(config["filter"])
            except ValueError:
                raise ValueError("Filter: Filter suffix is invalid: " +
                                 config["filter"])
            groups = str(ipSuffix)[1:].count(":")
            suffix = ipSuffix.exploded[groups * -5:]
        case "prefix":
            try:
                ipPrefix = ipaddress.ip_address(config["filter"])
            except ValueError:
                raise ValueError("Filter: Filter prefix is invalid: " +
                                 config["filter"])
            groups = str(ipPrefix)[:-1].count(":")
            prefix = ipPrefix.exploded[:groups * 5]
        case "subnet":
            try:
                subnet = ipaddress.ip_network(config["filter"], strict=False)
            except ValueError:
                raise ValueError("Filter: Filter subnet is invalid: " +
                                 config["filter"])
    translatedIps = []
    for ip in ipRecord[config["source"]]:
        ipAddr = ipaddress.ip_address(ip)
        match config["filterMethod"].lower():
            case "suffix":
                if ipAddr.exploded.endswith(suffix) ^ bool(config["invert"]):
                    translatedIps.append(ip)
            case "prefix":
                if ipAddr.exploded.startswith(prefix) ^ bool(config["invert"]):
                    translatedIps.append(ip)
            case "subnet":
                if (ipAddr in subnet) ^ bool(config["invert"]):
                    translatedIps.append(ip)
    return translatedIps
