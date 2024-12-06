# Extensible DDNS Script

A simple, extensible DDNS script designed to be easily modified to support any DNS provider, and any IP sources.

## Configuration

A [sample config file](config.sample.json) is provided with sample configurations for each supported DNS provider and IP source.

### IP Sources
- DNS
- SNMP
- Static IP
- Public Web Service

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
