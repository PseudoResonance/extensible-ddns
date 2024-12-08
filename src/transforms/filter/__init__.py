import ipaddress

from sources import SourceResult


async def transform_ips(config, ipRecord: dict[str, SourceResult], verbose=False):
    if config["source"] not in ipRecord:
        print(f"Filter: IP source does not exist: {config["source"]}")
        return SourceResult(False, [])
    if not ipRecord[config["source"]].status:
        print(f"Filter: IP source failed to run: {config["source"]}")
        return SourceResult(False, [])
    match config["filterMethod"].lower():
        case "suffix":
            try:
                ipSuffix = ipaddress.ip_address(config["filter"])
            except ValueError:
                print(f"Filter: Filter suffix is invalid: {config["filter"]}")
                return SourceResult(False, [])
            groups = str(ipSuffix)[1:].count(":")
            suffix = ipSuffix.exploded[groups * -5:]
        case "prefix":
            try:
                ipPrefix = ipaddress.ip_address(config["filter"])
            except ValueError:
                print(f"Filter: Filter prefix is invalid: {config["filter"]}")
                return SourceResult(False, [])
            groups = str(ipPrefix)[:-1].count(":")
            prefix = ipPrefix.exploded[:groups * 5]
        case "subnet":
            try:
                subnet = ipaddress.ip_network(
                    config["filter"], strict=False)
            except ValueError:
                print(f"Filter: Filter subnet is invalid: {config["filter"]}")
                return SourceResult(False, [])
    translatedIps = []
    for ip in ipRecord[config["source"]].ips:
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
    return SourceResult(True, translatedIps)
