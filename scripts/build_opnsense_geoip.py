#!/usr/bin/env python3
"""Build a MaxMind "GeoLite2-Country-CSV" archive from GeoLite2-Country.mmdb.

OPNsense's GeoIP alias backend (src/opnsense/scripts/filter/lib/alias/geoip.py)
consumes the ZIP that MaxMind ships for the GeoLite2-Country-CSV edition. It
locates members by case-insensitive substring of the *basename*:

    'locations-en.csv' -> geoname_id to country-code map
    'ipv4.csv'         -> IPv4 network blocks
    'ipv6.csv'         -> IPv6 network blocks

and it bails out silently when no locations member is found, so the member
names below are load-bearing, not cosmetic.

The parser splits every line on ',' rather than using a CSV reader, and reads
only fixed indices:

    locations: [0] geoname_id (must be digits)
               [2] continent_code (used as 'EU' fallback)
               [4] country_iso_code (must be len 2 and alnum)
    blocks:    [0] network
               [1] geoname_id (looked up in the locations map)

Every index it touches sits before country_name, which is the only field that
can legitimately contain a comma, so minimal quoting stays safe.
"""

import argparse
import csv
import os
import sys

import maxminddb

LOCATIONS_HEADER = [
    'geoname_id',
    'locale_code',
    'continent_code',
    'continent_name',
    'country_iso_code',
    'country_name',
    'is_in_european_union',
]

BLOCKS_HEADER = [
    'network',
    'geoname_id',
    'registered_country_geoname_id',
    'represented_country_geoname_id',
    'is_anonymous_proxy',
    'is_satellite_provider',
]

LOCATIONS_NAME = 'GeoLite2-Country-Locations-en.csv'
BLOCKS_V4_NAME = 'GeoLite2-Country-Blocks-IPv4.csv'
BLOCKS_V6_NAME = 'GeoLite2-Country-Blocks-IPv6.csv'


def _writer(handle):
    # LF endings: OPNsense splits on '\n', so CRLF would leave a stray '\r'
    # glued to the final column of every row.
    return csv.writer(handle, lineterminator='\n')


def _record_location(locations, country, continent):
    """Remember one geoname -> country mapping, upgrading a partial entry."""
    if not country:
        return
    geoname_id = country.get('geoname_id')
    iso_code = country.get('iso_code')
    if not geoname_id or not iso_code:
        return

    existing = locations.get(geoname_id)
    # A registered_country record carries no continent of its own; prefer the
    # first entry that has one rather than letting a later blank overwrite it.
    if existing and existing[0]:
        return

    locations[geoname_id] = (
        (continent or {}).get('code', ''),
        (continent or {}).get('names', {}).get('en', ''),
        iso_code,
        country.get('names', {}).get('en', ''),
        '1' if country.get('is_in_european_union') else '0',
    )


def build(mmdb_path, out_dir):
    reader = maxminddb.open_database(mmdb_path)
    build_epoch = reader.metadata().build_epoch

    os.makedirs(out_dir, exist_ok=True)
    locations = {}
    counts = {'IPv4': 0, 'IPv6': 0}

    v4_path = os.path.join(out_dir, BLOCKS_V4_NAME)
    v6_path = os.path.join(out_dir, BLOCKS_V6_NAME)

    with open(v4_path, 'w', newline='', encoding='utf-8') as f4, \
            open(v6_path, 'w', newline='', encoding='utf-8') as f6:
        w4, w6 = _writer(f4), _writer(f6)
        w4.writerow(BLOCKS_HEADER)
        w6.writerow(BLOCKS_HEADER)

        for network, data in reader:
            country = data.get('country')
            registered = data.get('registered_country')
            represented = data.get('represented_country')
            continent = data.get('continent')

            _record_location(locations, country, continent)
            _record_location(locations, registered, None)
            _record_location(locations, represented, None)

            network = str(network)
            proto = 'IPv6' if ':' in network else 'IPv4'
            # Mirrors MaxMind exactly: geoname_id is blank when the network has
            # no country record, and OPNsense then skips the row. Only ~0.2% of
            # networks are registered_country-only, so this costs almost nothing
            # and keeps the file honest.
            (w6 if proto == 'IPv6' else w4).writerow([
                network,
                (country or {}).get('geoname_id', ''),
                (registered or {}).get('geoname_id', ''),
                (represented or {}).get('geoname_id', ''),
                1 if data.get('traits', {}).get('is_anonymous_proxy') else 0,
                1 if data.get('traits', {}).get('is_satellite_provider') else 0,
            ])
            counts[proto] += 1

    reader.close()

    loc_path = os.path.join(out_dir, LOCATIONS_NAME)
    with open(loc_path, 'w', newline='', encoding='utf-8') as fl:
        wl = _writer(fl)
        wl.writerow(LOCATIONS_HEADER)
        for geoname_id in sorted(locations):
            cont_code, cont_name, iso, name, in_eu = locations[geoname_id]
            wl.writerow([geoname_id, 'en', cont_code, cont_name, iso, name, in_eu])

    return {
        'build_epoch': build_epoch,
        'locations': len(locations),
        'IPv4': counts['IPv4'],
        'IPv6': counts['IPv6'],
        'paths': [loc_path, v4_path, v6_path],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mmdb', default='v2/GeoLite2-Country.mmdb')
    parser.add_argument('--out-dir', default='tmp/opnsense')
    parser.add_argument('--min-networks', type=int, default=100000)
    parser.add_argument('--epoch-file', help='write the MMDB build_epoch here')
    args = parser.parse_args()

    stats = build(args.mmdb, args.out_dir)
    total = stats['IPv4'] + stats['IPv6']

    print(f"locations : {stats['locations']}")
    print(f"IPv4      : {stats['IPv4']}")
    print(f"IPv6      : {stats['IPv6']}")
    print(f"total     : {total}")
    print(f"build_epoch: {stats['build_epoch']}")

    if args.epoch_file:
        with open(args.epoch_file, 'w', encoding='utf-8') as fh:
            fh.write(str(stats['build_epoch']))

    if total < args.min_networks:
        print(f"ERROR: only {total} networks, expected >= {args.min_networks}")
        return 1
    if stats['locations'] < 100:
        print(f"ERROR: only {stats['locations']} locations, expected >= 100")
        return 1
    if stats['IPv4'] == 0 or stats['IPv6'] == 0:
        print("ERROR: one of the address families is empty")
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
