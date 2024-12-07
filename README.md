# Extensible DDNS Script

A simple, extensible DDNS script designed to be easily modified to support any DNS provider, and any IP sources.

## Configuration

A [sample config file](config.sample.json) is provided with sample configurations for each supported DNS provider, IP source and IP transform.

### IP Sources
- DNS
- SNMP
- Static IP
- Public Web Service

### IP Transformations
- Track IPv6

### Sinks/DNS Providers
- Cloudflare
- RFC2136

### Config Format

#### Sources

The `sources` section defines where IPs are fetched from. The following is an example source configuration:

```json
"sources": {
    "server": {
        "type": "dns",
        "dnsServer": "10.0.0.1",
        "domain": "server.internal",
        "ipType": "AAAA"
    }
}
```

Each source is referenced by its name, in this case `server`. It has a type of `dns`, meaning it will use a DNS server to fetch IPs. In this case, it will contact the server at `10.0.0.1` for all `AAAA` or IPv6 records for the domain `server.internal`.

#### Transforms

The `transforms` section defines which sources IPs are taken from, and how they will be modified. The following is an example transform configuration:

```json
"transforms": {
    "trackip": {
        "type": "trackipv6",
        "trackSource": "routerv6",
        "trackPrefixLength": 64,
        "ipSource": "server"
    }
}
```

Each transform is referenced by its name, in this case `trackip`. It has a type of `trackipv6`, meaning it will take in a list of IPv6 IPs, and replace their prefix with the prefix from the tracking source. This is used in conjunction with NPTv6 prefix translation. In this case, it will get the list of IPs from `routerv6`. Because IP lists may contain multiple IPs, it is recommended to first use a filter transform to filter out only the desired IP. In the event that there are multiple IPs present though, the first IP will be chosen to track the prefix. The prefix is then calculated based on the prefix length, and applied to all internal IPs.

NOTE: Currently transformations are processed in the same order they are defined in the config. This means that if you want to chain transformations, the first transformation must be listed first, and the one that depends on it must come after.

#### Sinks/DNS Providers

The `sinks` section defines the DNS providers that the IPs will be sent to. The following is an example sink configuration:

```json
"sinks": {
    "main": {
        "type": "cloudflare",
        "apiToken": "API_TOKEN_HERE",
        "zones": [
            {
                "name": "example.com",
                "records": [
                    {
                        "domain": "server",
                        "sources": {
                            "AAAA": "server"
                        },
                        "ttl": 60,
                        "extra": {
                            "proxied": true
                        }
                    }
                ]
            }
        ]
    }
}
```

Each sink is referenced by its name, in this case `main`. It has a type of `cloudflare`, meaning it will use the Cloudflare API to update records. The API token must be provided, or the account email and API key to authenticate requests.

The `zones` section lists all DNS zones that need updating. One zone is listed here, with the name `example.com`, and 1 record at the subdomain `server`. This will translate to `server.example.com` The record should have a TTL of 60 seconds, it should be proxied by Cloudflare, and it should get `AAAA` or IPv6 records from the `server` source configured above.
