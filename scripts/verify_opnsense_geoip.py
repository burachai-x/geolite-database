#!/usr/bin/env python3
"""Verify a ZIP really is consumable by OPNsense's GeoIP alias backend.

This deliberately re-implements the matching and parsing of
src/opnsense/scripts/filter/lib/alias/geoip.py (process_zip) instead of just
sanity-checking our own output, because the failure mode we care about is
silent: when no '*locations-en.csv' member is present OPNsense parses nothing,
raises nothing, and simply produces zero country files.
"""

import argparse
import ipaddress
import os
import sys
import zipfile

# Countries that must show up, so a structurally valid but semantically empty
# archive still fails the build.
EXPECTED_COUNTRIES = ['TH', 'US', 'JP', 'CN', 'DE', 'GB', 'SG']


def verify(zip_path):
    result = {
        'address_count': 0,
        'file_count': 0,
        'timestamp': None,
        'locations_filename': None,
        'address_sources': {'IPv4': None, 'IPv6': None},
    }
    countries = {}

    with zipfile.ZipFile(zip_path, mode='r') as zf:
        file_handles = {}
        for item in zf.infolist():
            if item.file_size > 0:
                filename = os.path.basename(item.filename)
                file_handles[filename] = item
                if filename.lower().find('locations-en.csv') > -1:
                    result['locations_filename'] = filename
                elif filename.lower().find('ipv4.csv') > -1:
                    result['address_sources']['IPv4'] = filename
                elif filename.lower().find('ipv6.csv') > -1:
                    result['address_sources']['IPv6'] = filename

        if result['locations_filename'] is None:
            print('FAIL: no *locations-en.csv member; OPNsense would parse nothing')
            return None, None

        import datetime
        result['timestamp'] = datetime.datetime(
            *file_handles[result['locations_filename']].date_time
        ).isoformat()

        country_codes = {}
        locations = zf.open(file_handles[result['locations_filename']]).read()
        for line in locations.decode().split('\n'):
            parts = line.split(',')
            if len(parts) > 4 and parts[0].isdigit():
                if len(parts[4]) == 2 and parts[4].isalnum():
                    country_codes[parts[0]] = parts[4]
                elif parts[2] == 'EU':
                    country_codes[parts[0]] = parts[2]

        for proto in ['IPv4', 'IPv6']:
            if result['address_sources'][proto] is None:
                print(f'FAIL: no {proto} blocks member')
                return None, None
            seen = set()
            blocks = zf.open(file_handles[result['address_sources'][proto]]).read()
            for line in blocks.decode().split('\n'):
                parts = line.split(',')
                if len(parts) > 1 and parts[1] in country_codes:
                    code = country_codes[parts[1]]
                    key = f'{code}-{proto}'
                    if key not in seen:
                        seen.add(key)
                        result['file_count'] += 1
                    countries.setdefault(code, {'IPv4': 0, 'IPv6': 0})
                    countries[code][proto] += 1
                    result['address_count'] += 1
                    # OPNsense revalidates each line with ipaddress.ip_network
                    # at alias-build time (iter_addresses); a row that fails
                    # there is dropped silently, so check it here.
                    try:
                        ipaddress.ip_network(parts[0].strip(), strict=False)
                    except (ipaddress.AddressValueError, ValueError):
                        print(f'FAIL: {proto} row is not a valid network: {parts[0]!r}')
                        return None, None

    return result, countries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip_path')
    parser.add_argument('--min-addresses', type=int, default=100000)
    # Opt-in: OPNsense maps continent-level rows (blank ISO code, continent
    # 'EU') to a synthetic 'EU' country. The P3TERX-built MMDB gives every
    # network a real country, so nothing lands there and this stays off.
    parser.add_argument('--expect-eu', action='store_true')
    args = parser.parse_args()

    result, countries = verify(args.zip_path)
    if result is None:
        return 1

    print(f"timestamp     : {result['timestamp']}")
    print(f"locations     : {result['locations_filename']}")
    print(f"IPv4 source   : {result['address_sources']['IPv4']}")
    print(f"IPv6 source   : {result['address_sources']['IPv6']}")
    print(f"country files : {result['file_count']}")
    print(f"addresses     : {result['address_count']}")

    ok = True
    if result['address_count'] < args.min_addresses:
        print(f"FAIL: {result['address_count']} addresses < {args.min_addresses}")
        ok = False

    for code in EXPECTED_COUNTRIES:
        entry = countries.get(code)
        if not entry or entry['IPv4'] == 0 or entry['IPv6'] == 0:
            print(f'FAIL: {code} missing or has an empty address family: {entry}')
            ok = False
        else:
            print(f"  {code}: IPv4={entry['IPv4']} IPv6={entry['IPv6']}")

    if args.expect_eu and 'EU' not in countries:
        print('FAIL: no EU continent-level entries resolved')
        ok = False

    print('PASS: archive parses as OPNsense would parse it' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
