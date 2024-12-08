import ipaddress
import pysnmp.hlapi.v3arch.asyncio as pysnmp

from sources import SourceResult


async def snmp_fetch_ip_dict(config):
    """
    Fetch a dict mapping each interface ID to lists of the associated IPv4 and IPv6.
    """
    snmpEngine = pysnmp.SnmpEngine()
    # Interface IPs OID
    initialVarBinds = "1.3.6.1.2.1.4.34.1.3"
    varBinds = pysnmp.ObjectType(pysnmp.ObjectIdentity(initialVarBinds))
    results = dict()
    while True:
        iterator = pysnmp.bulk_cmd(
            snmpEngine,
            pysnmp.CommunityData(config["community"], mpModel=1),
            await pysnmp.UdpTransportTarget.create((config["target"], config["port"])),
            pysnmp.ContextData(),
            0,
            50,
            varBinds,
            lookupMib=False,
        )
        errorIndication, errorStatus, errorIndex, varBindTable = await iterator
        if errorIndication:
            print(errorIndication)
            break
        elif errorStatus:
            print(f"{errorStatus.prettyPrint()} at {
                errorIndex and varBinds[int(errorIndex) - 1][0] or "?"}")
        else:
            for varBind in varBindTable:
                if varBind[0].prettyPrint().startswith(initialVarBinds):
                    # Strip the prefix and keep only the IP data
                    data = varBind[0][12:]
                    # varBind[1] contains the interface ID
                    results.setdefault(int(varBind[1]), {"A": [], "AAAA": []})
                    # varbind[0][10] is the IP type, 1 for IPv4 and 2 for IPv6
                    if varBind[0][10] == 1:
                        # Format IPv4 in human format
                        ipAddress = ".".join(map(str, data))
                        try:
                            results[int(varBind[1])]["A"].append(
                                str(ipaddress.ip_address(ipAddress)))
                        except ValueError:
                            print(f"SNMP: Invalid IP: {ipAddress}")
                    elif varBind[0][10] == 2:
                        # Format IPv6 in human format
                        ipAddress = ":".join(
                            format(x, "x").zfill(2) + format(y, "x").zfill(2)
                            for x, y in zip(data[0::2], data[1::2])
                        )
                        try:
                            results[int(varBind[1])]["AAAA"].append(
                                str(ipaddress.ip_address(ipAddress)))
                        except ValueError:
                            print(f"SNMP: Invalid IP: {ipAddress}")

                else:
                    # Stop when returned OID is no longer within desired range
                    snmpEngine.close_dispatcher()
                    return results
        varBinds = varBindTable[-1]
        if pysnmp.is_end_of_mib(varBindTable):
            break
    snmpEngine.close_dispatcher()
    return results


async def snmp_fetch_interface_dict(config):
    snmpEngine = pysnmp.SnmpEngine()
    # Interface name to ID OID
    initialVarBinds = "1.3.6.1.2.1.2.2.1.2"
    varBinds = pysnmp.ObjectType(pysnmp.ObjectIdentity(initialVarBinds))
    results = dict()
    while True:
        iterator = pysnmp.bulk_cmd(
            snmpEngine,
            pysnmp.CommunityData(config["community"], mpModel=1),
            await pysnmp.UdpTransportTarget.create((config["target"], config["port"])),
            pysnmp.ContextData(),
            0,
            50,
            varBinds,
            lookupMib=False,
        )
        errorIndication, errorStatus, errorIndex, varBindTable = await iterator
        if errorIndication:
            print(errorIndication)
            break
        elif errorStatus:
            print(f"{errorStatus.prettyPrint()} at {
                errorIndex and varBinds[int(errorIndex) - 1][0] or "?"}")
        else:
            for varBind in varBindTable:
                if varBind[0].prettyPrint().startswith(initialVarBinds):
                    # varbind[0][-1] is the interface ID
                    # varbind[1] is the interface name
                    results[varBind[0][-1]] = str(varBind[1])
                else:
                    # Stop when returned OID is no longer within desired range
                    snmpEngine.close_dispatcher()
                    return results
        varBinds = varBindTable[-1]
        if pysnmp.is_end_of_mib(varBindTable):
            break
    snmpEngine.close_dispatcher()
    return results


async def fetch_ip(config, verbose=False):
    try:
        interfaces = await snmp_fetch_interface_dict(config)
        id = -1
        for x in interfaces:
            if interfaces[x] == config["interfaceName"]:
                id = int(x)
        if id < 0:
            raise ValueError(f"Unable to find interface {
                             config["interfaceName"]}")
        ips = await snmp_fetch_ip_dict(config)
        if id in ips:
            if config["ipType"] in ips[id]:
                return SourceResult(True, ips[id][config["ipType"]])
        raise ValueError(
            f"Unable to find {config["ipType"]} type for interface {
                config["interfaceName"]}"
        )
    except Exception as e:
        print(f"SNMP: Error while fetching IPs: {e}")
        return SourceResult(False, [])
