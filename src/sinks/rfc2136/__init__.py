from dataclasses import dataclass
import dataclasses
import json
import dns.query
import dns.zone
import dns.tsigkeyring
import dns.update
import dns.xfr
import dns.name
import dns.rdatatype
import dns.rdata
import dns.rdataclass
import dns.rdtypes
from frozendict import frozendict
import util.records

TXT_PREFIX = "ddns-managed-"


@dataclass(frozen=True)
class ManagedRecord:
    name: str
    type: str
    ttl: int
    content: str


def decode_json(rData) -> ManagedRecord:
    return json.loads(
        "{" + b"".join(rData.strings).decode("utf-8").lower() + "}", object_hook=lambda d: ManagedRecord(**d))


def encode_json(data: ManagedRecord) -> str:
    return json.dumps(dataclasses.asdict(data), separators=(',', ':'))[1:-1]


async def update_ips(config, ipRecord, dryrun=False, verbose=False):
    tsig_keyring = dns.tsigkeyring.from_text(
        {config["keyName"]: config["keySecret"]}
    )
    finalZoneState = []
    for zone in config["zones"]:
        zoneName = dns.name.from_text(zone["name"])
        plan = util.records.calculate_records(zone["records"], ipRecord)
        if verbose:
            print("RFC2136: Planned records:", plan)
        state = []
        dnsZone = dns.zone.Zone(zoneName)
        dnsQuery, _ = dns.xfr.make_query(
            dnsZone, keyring=tsig_keyring)
        dns.query.inbound_xfr(
            where=config["host"], txn_manager=dnsZone, query=dnsQuery, port=53, timeout=5)
        managedRecords: list[ManagedRecord] = []
        for recordName, _, rData in dnsZone.iterate_rdatas(dns.rdatatype.TXT):
            try:
                if recordName.to_text().startswith(TXT_PREFIX):
                    managedRecords.append(decode_json(rData))
            except Exception as e:
                print("RFC2136: Error decoding comment for record: " +
                      recordName.to_text(), e)
        for recordName, ttl, rData in dnsZone.iterate_rdatas():
            try:
                searchRecord = None
                match rData.rdtype:
                    case dns.rdatatype.A | dns.rdatatype.AAAA:
                        searchRecord = ManagedRecord(recordName.to_text().lower(
                        ), dns.rdatatype.to_text(rData.rdtype).lower(), ttl, rData.to_text().lower())
                    case _:
                        continue
                if searchRecord in managedRecords:
                    state.append(util.records.Record(searchRecord.content, searchRecord.type.upper(),
                                                     searchRecord.name, ttl, frozendict({}), frozendict({})))
                    managedRecords.remove(searchRecord)
            except Exception as e:
                print("RFC2136: Error checking record: " +
                      recordName.to_text(), e)
        if len(managedRecords) > 0:
            print("RFC2136: Unable to find the following records:", managedRecords)
        if verbose:
            print("RFC2136: Current records:", state)
        _, to_add, to_delete = util.records.calculate_diff(plan, state)
        if verbose:
            print("RFC2136: Records to delete:", to_delete)
            print("RFC2136: Records to add:", to_add)
        for record in to_delete:
            if dryrun:
                print(f"RFC2136: Deleting zone:{zone["name"]} name:{record.domain} type:{
                      record.type} content:{record.content} ttl:{record.ttl}")
                state.remove(record)
            else:
                update = dns.update.Update(
                    zoneName,
                    keyring=tsig_keyring,
                )
                update.delete(record.domain, dns.rdata.from_text(
                    rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.from_text(record.type), origin=zoneName, tok=record.content))
                update.delete(f"{TXT_PREFIX}{record.type.lower()}-{record.domain.lower()}",
                              dns.rdtypes.ANY.TXT.TXT(
                    rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.TXT, strings=[encode_json(ManagedRecord(record.domain.lower(), record.type.lower(), record.ttl, record.content.lower()))]))
                result = dns.query.tcp(update, config["host"], timeout=5)
                if result.rcode().value == 0:
                    state.remove(record)
                else:
                    print(f"RFC2136: Error while deleting record zone:{zone["name"]} name:{record.domain} type:{
                        record.type} content:{record.content} ttl:{record.ttl}")
        for record in to_add:
            if dryrun:
                print(f"RFC2136: Adding zone:{zone["name"]} name:{record.domain} type:{
                      record.type} content:{record.content} ttl:{record.ttl}")
                state.append(util.records.Record(record.content, record.type,
                                                 record.domain, record.ttl, record.extra, frozendict({})))
            else:
                update = dns.update.Update(
                    zoneName,
                    keyring=tsig_keyring,
                )
                update.add(record.domain, record.ttl,
                           dns.rdata.from_text(rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.from_text(record.type), origin=zoneName, tok=record.content))
                update.add(f"{TXT_PREFIX}{record.type.lower()}-{record.domain.lower()}", 0, dns.rdtypes.ANY.TXT.TXT(
                    rdclass=dns.rdataclass.IN, rdtype=dns.rdatatype.TXT, strings=[encode_json(ManagedRecord(record.domain.lower(), record.type.lower(), record.ttl, record.content.lower()))]))
                result = dns.query.tcp(update, config["host"], timeout=5)
                if result.rcode().value == 0:
                    state.append(util.records.Record(record.content, record.type,
                                                     record.domain, record.ttl, record.extra, frozendict({})))
                else:
                    print(f"RFC2136: Error while adding record zone:{zone["name"]} name:{record.domain} type:{
                        record.type} content:{record.content} ttl:{record.ttl}")
        if verbose:
            print("RFC2136: Final state:", state)
        finalZoneState.append({"name": zone["name"], "records": state})
    return finalZoneState
