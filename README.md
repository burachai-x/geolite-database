# GeoIP Database Mirror

Auto-synced mirror of GeoIP databases (both legacy v1 and GeoLite2 v2), updated daily via GitHub Actions.

## v1 — GeoIP Legacy (.dat.gz)

Source: [mailfud.org/geoip-legacy](https://mailfud.org/geoip-legacy/)

| File | Description |
|------|-------------|
| `v1/GeoIP.dat.gz` | Country — IPv4 |
| `v1/GeoIPv6.dat.gz` | Country — IPv6 |
| `v1/GeoIPCity.dat.gz` | City — IPv4 |
| `v1/GeoIPCityv6.dat.gz` | City — IPv6 |
| `v1/GeoIPASNum.dat.gz` | ASN — IPv4 |
| `v1/GeoIPASNumv6.dat.gz` | ASN — IPv6 |
| `v1/GeoIPISP.dat.gz` | ISP — IPv4 |
| `v1/GeoIPISPv6.dat.gz` | ISP — IPv6 |
| `v1/GeoIPOrg.dat.gz` | Organization — IPv4 |
| `v1/GeoIPOrgv6.dat.gz` | Organization — IPv6 |

```
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIP.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPv6.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPCity.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPCityv6.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPASNum.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPASNumv6.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPISP.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPISPv6.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPOrg.dat.gz
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v1/GeoIPOrgv6.dat.gz
```

## v2 — GeoLite2 (.mmdb)

Source: [P3TERX/GeoLite.mmdb](https://github.com/P3TERX/GeoLite.mmdb) (upstream: [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data))

| File | Description |
|------|-------------|
| `v2/GeoLite2-ASN.mmdb` | IP → ASN (Autonomous System Number) |
| `v2/GeoLite2-City.mmdb` | IP → City, region, latitude/longitude |
| `v2/GeoLite2-Country.mmdb` | IP → Country |

```
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v2/GeoLite2-ASN.mmdb
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v2/GeoLite2-City.mmdb
https://raw.githubusercontent.com/burachai-x/geolite-database/main/v2/GeoLite2-Country.mmdb
```

## csv — GeoLite2 Country CSV (OPNsense GeoIP alias)

Generated from `v2/GeoLite2-Country.mmdb`, laid out exactly like MaxMind's
`GeoLite2-Country-CSV` edition so OPNsense's GeoIP alias backend can consume it
without a MaxMind account.

| File | Description |
|------|-------------|
| `csv/GeoLite2-Country-CSV.zip` | `Locations-en` + `Blocks-IPv4` + `Blocks-IPv6` |

Paste this into **Firewall → Aliases → GeoIP settings → URL**, then apply:

```
https://raw.githubusercontent.com/burachai-x/geolite-database/main/csv/GeoLite2-Country-CSV.zip
```

Notes:

- The URL **must** end in `.zip`. `raw.githubusercontent.com` sends no
  `Content-Disposition` header, so OPNsense falls through to its ZIP branch —
  a `.gz` feed would be handed to `zipfile` and fail.
- Networks that carry only a `registered_country` (~0.2%) have a blank
  `geoname_id` and are skipped by OPNsense, matching genuine MaxMind behaviour.
- Archive members are stamped with the MMDB's `build_epoch`, so OPNsense reports
  the real database date and unchanged data produces a byte-identical ZIP.

## Update Schedule

Runs daily at **20:13 UTC** (03:13 ICT next day). Only commits when databases change.

## License

- **GeoLite2 (v2)**: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) — requires attribution to MaxMind
- **GeoIP Legacy (v1)**: Originally MaxMind, redistributed via mailfud.org for non-commercial use
