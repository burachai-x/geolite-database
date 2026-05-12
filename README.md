# GeoLite2 Database Mirror

Auto-synced mirror of [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) databases, updated daily via GitHub Actions. Source: [P3TERX/GeoLite.mmdb](https://github.com/P3TERX/GeoLite.mmdb).

## Databases

| File | Description |
|------|-------------|
| `v2/GeoLite2-ASN.mmdb` | IP → ASN (Autonomous System Number) |
| `v2/GeoLite2-City.mmdb` | IP → City, region, latitude/longitude |
| `v2/GeoLite2-Country.mmdb` | IP → Country |

## Download

Use the raw GitHub URL to download directly:

```
https://raw.githubusercontent.com/burachai-x/geolite2-database/main/v2/GeoLite2-ASN.mmdb
https://raw.githubusercontent.com/burachai-x/geolite2-database/main/v2/GeoLite2-City.mmdb
https://raw.githubusercontent.com/burachai-x/geolite2-database/main/v2/GeoLite2-Country.mmdb
```

## Update Schedule

Runs daily at **00:00 UTC** (07:00 ICT). Only commits when the database changes.

## License

GeoLite2 databases are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) and require attribution to MaxMind.
