import json
import cloudflare
from frozendict import frozendict
import cloudflare.lib
from sources import SourceResult
import util.records

MANAGEMENT_COMMENT_SEARCH = {"startswith": "Managed by DDNS "}
MANAGEMENT_COMMENT_PREFIX = "Managed by DDNS "


async def update_ips(config, ipRecord: dict[str, SourceResult], dryrun=False, verbose=False):
    if "apiToken" in config and len(config["apiToken"]) > 0:
        client = cloudflare.Cloudflare(
            api_token=config["apiToken"]
        )
    else:
        client = cloudflare.Cloudflare(
            api_email=config["apiEmail"],
            api_key=config["apiKey"]
        )
    zoneMapping = dict()
    finalZoneState = []
    for zone in client.zones.list():
        zoneMapping[zone.name] = zone.id
    for zone in config["zones"]:
        if zone["name"] not in zoneMapping:
            print(f"Cloudflare: Zone {zone["name"]} does not exist.")
            continue
        zone_id = zoneMapping[zone["name"]]
        plan, ignored_sources = util.records.calculate_records(
            zone["records"], ipRecord)
        if verbose:
            print("Cloudflare: Planned records:", plan)
        state = []
        for record in client.dns.records.list(zone_id=zone_id, comment=MANAGEMENT_COMMENT_SEARCH):
            try:
                data = json.loads(record.comment.removeprefix(
                    MANAGEMENT_COMMENT_PREFIX))
                if data["source"] not in ignored_sources:
                    state.append(util.records.Record(record.content, record.type,
                                                     record.name.removesuffix("." + zone["name"]), record.ttl, frozendict({"proxied": record.proxied}), frozendict({"id": record.id, "source": data["source"]})))
            except Exception:
                print(f"Cloudflare: Error parsing record data: id:{record.id} type:{
                      record.type} ttl:{record.ttl} name:{record.name} content:{record.content}")
        if verbose:
            print("Cloudflare: Current records:", state)
        to_update, to_add, to_delete = util.records.calculate_diff(
            plan, state, can_update=True)
        if verbose:
            print("Cloudflare: Records to update:", to_update)
            print("Cloudflare: Records to delete:", to_delete)
            print("Cloudflare: Records to add:", to_add)
        for recordSet in to_update:
            record = recordSet.updated
            if dryrun:
                print(f"Cloudflare: Updating dns_record_id:{recordSet.current.internal["id"]} zone_id:{zone_id} name:{record.domain} type:{
                      record.type} content:{record.content} ttl:{record.ttl} proxied:{record.extra["proxied"]}")
                state.remove(recordSet.current)
                state.append(util.records.Record(recordSet.updated.content, recordSet.updated.type,
                                                 recordSet.updated.domain, recordSet.updated.ttl, recordSet.updated.extra, recordSet.current.internal))
            else:
                try:
                    client.dns.records.update(
                        zone_id=zone_id, dns_record_id=recordSet.current.internal["id"], type=record.type, comment=f"{MANAGEMENT_COMMENT_PREFIX}{json.dumps({"source": record.internal["source"]})}", name=record.domain, content=record.content, ttl=record.ttl, proxied=record.extra["proxied"])
                    print("Cloudflare: Success")
                    state.remove(recordSet.current)
                    state.append(util.records.Record(recordSet.updated.content, recordSet.updated.type,
                                                     recordSet.updated.domain, recordSet.updated.ttl, recordSet.updated.extra, recordSet.current.internal))
                except cloudflare.APIConnectionError as e:
                    print("Cloudflare: The server could not be reached")
                    print(e.__cause__)
                except cloudflare.RateLimitError as e:
                    print("Cloudflare: API rate limited")
                    break
                except cloudflare.APIStatusError as e:
                    print(f"Cloudflare: Error while updating record dns_record_id:{recordSet.current.internal["id"]} zone_id:{zone_id} name:{record.domain} type:{
                        record.type} content:{record.content} ttl:{record.ttl} proxied:{record.extra["proxied"]}")
                    print(e.status_code)
                    print(e.response)
        for record in to_delete:
            if dryrun:
                print(f"Cloudflare: Deleting dns_record_id:{record.internal["id"]} zone_id:{zone_id} name:{record.domain} type:{
                      record.type} content:{record.content} ttl:{record.ttl} proxied:{record.extra["proxied"]}")
                state.remove(record)
            else:
                try:
                    client.dns.records.delete(
                        zone_id=zone_id, dns_record_id=record.internal["id"])
                    print("Cloudflare: Success")
                    state.remove(record)
                except cloudflare.APIConnectionError as e:
                    print("Cloudflare: The server could not be reached")
                    print(e.__cause__)
                except cloudflare.RateLimitError as e:
                    print("Cloudflare: API rate limited")
                    break
                except cloudflare.APIStatusError as e:
                    print(f"Cloudflare: Error while deleting record dns_record_id:{recordSet.current.internal["id"]} zone_id:{zone_id} name:{record.domain} type:{
                        record.type} content:{record.content} ttl:{record.ttl} proxied:{record.extra["proxied"]}")
                    print(e.status_code)
                    print(e.response)
        for record in to_add:
            if dryrun:
                print(f"Cloudflare: Adding zone_id:{zone_id} name:{record.domain} type:{
                      record.type} content:{record.content} ttl:{record.ttl} proxied:{record.extra["proxied"]}")
                state.append(util.records.Record(record.content, record.type,
                                                 record.domain, record.ttl, record.extra, frozendict({})))
            else:
                try:
                    newRecord = client.dns.records.create(
                        zone_id=zone_id, comment=f"{MANAGEMENT_COMMENT_PREFIX}{json.dumps({"source": record.internal["source"]})}", name=record.domain, type=record.type, content=record.content, ttl=record.ttl, proxied=record.extra["proxied"])
                    if newRecord is not None:
                        print("Cloudflare: Success")
                        state.append(util.records.Record(record.content, record.type,
                                                         record.domain, record.ttl, record.extra, frozendict({"id": newRecord.id})))
                    else:
                        print("Cloudflare: Unable to fetch updated record")
                except cloudflare.APIConnectionError as e:
                    print("Cloudflare: The server could not be reached")
                    print(e.__cause__)
                except cloudflare.RateLimitError as e:
                    print("Cloudflare: API rate limited")
                    break
                except cloudflare.APIStatusError as e:
                    print(f"Cloudflare: Error while adding record zone_id:{zone_id} name:{record.domain} type:{
                        record.type} content:{record.content} ttl:{record.ttl} proxied:{record.extra["proxied"]}")
                    print(e.status_code)
                    print(e.response)
        if verbose:
            print("Cloudflare: Final state:", state)
        finalZoneState.append({"name": zone["name"], "records": state})
    return finalZoneState
