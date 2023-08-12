#!/usr/bin/env python3

# This file is licensed under BSD 3-Clause.
# All license information is available in the included COPYING file.

#
# gogify.py
#
# Author       : Finn Rayment <finn@rayment.fr>
# Date created : 12/08/2023
#


import argparse
import json
import sys
import urllib.parse
import xml.sax.saxutils

import requests
import tabulate

import utils


API_SEARCH = 'https://embed.gog.com/games/ajax/filtered?mediaType=game&search=%s'
API_DOWNLOADS = 'https://api.gog.com/products/%d?expand=downloads'
DEFAULT_TIMEOUT = 10
VERSION = '1.0.0'

parser = argparse.ArgumentParser(
    prog=sys.argv[0],
    description='Dump available product versions from GOG.',
    epilog='Copyright (c) 2023 - Finn Rayment',
    add_help=False
)
parser.add_argument(
    '--help',
    action='help',
    help='show this help message and exit'
)
parser.add_argument(
    '-h', '--human-readable',
    action='store_true',
    help='show file sizes in human-readable format'
)
parser.add_argument(
    '-o', '--output',
    choices=['csv', 'json', 'pipe', 'table', 'xml'],
    default='table',
    help='output format (default: table)'
)
parser.add_argument(
    '-p', '--platform',
    choices=['windows', 'linux', 'mac', 'all'],
    help='only show versions for a given platform'
)
parser.add_argument(
    '-s', '--suppress',
    action='store_true',
    help='suppress errors if search returns no results'
)
parser.add_argument(
    '-t', '--timeout',
    type=utils.check_positive,
    metavar='sec',
    default=10,
    help=f'number of seconds to wait for a connection before timeout (default: {DEFAULT_TIMEOUT})'
)
parser.add_argument(
    '-v', '--version',
    action='version',
    version=f'{sys.argv[0]} - v{VERSION}'
)
parser.add_argument(
    'appname',
    help='search terms for application name'
)
parser.add_argument(
    'remainder',
    nargs=argparse.REMAINDER,
    help=argparse.SUPPRESS
)

args = parser.parse_args()

os_detect = utils.os_detect(suppress=args.suppress)


def get_products(search):
    uri_term = urllib.parse.quote(search)
    try:
        r = requests.get(API_SEARCH % uri_term, timeout=args.timeout)
    except requests.exceptions.ConnectionError:
        if not args.suppress:
            print('Failed to connect to GOG API for product search.')
        sys.exit(1)
    except requests.exceptions.ReadTimeout:
        if not args.suppress:
            print('Timeout occurred while trying to connect to GOG API for product search.')
        sys.exit(1)
    if r.status_code == 200:
        response = r.json()
        if 'products' in response:
            products = response['products']
            product_ids = []
            for product in products:
                if 'id' in product:
                    product_ids.append(product['id'])
            return product_ids
    else:
        if not args.suppress:
            print(f'GOG API returned unexpected status code {r.status_code} for product search!')
        sys.exit(1)
    return None


def get_installers(appid):
    try:
        r = requests.get(API_DOWNLOADS % appid, timeout=args.timeout)
    except requests.exceptions.ConnectionError:
        if not args.suppress:
            print('Failed to connect to GOG API for product inspection.')
        sys.exit(1)
    except requests.exceptions.ReadTimeout:
        if not args.suppress:
            print('Timeout occurred while trying to connect to GOG API for product inspection.')
        sys.exit(1)
    if r.status_code == 200:
        response = r.json()
        if 'downloads' in response and 'installers' in response['downloads']:
            return response['downloads']['installers']
    else:
        if not args.suppress:
            print(f'GOG API returned unexpected status code {r.status_code} for product inspection!')
        sys.exit(1)
    return None


args.remainder.insert(0, args.appname)
search_term = ' '.join([x for x in args.remainder if x])
products = get_products(search_term)

installers = []
for product in products:
    installers += get_installers(product)
metadata = []
for installer in installers:
    name = utils.keydic('name', installer, default='?')
    version = utils.keydic('version', installer, default='?')
    platform = utils.keydic('os', installer, default='?')
    lang = utils.keydic('language', installer, default='?')
    size = utils.keydic('total_size', installer, default='?')
    if args.human_readable:
        size = utils.sizeof_fmt(size)
    if args.platform == 'all' or platform == args.platform or (args.platform is None and platform == os_detect):
        metadata.append({'name': name, 'version': version, 'platform': platform, 'lang': lang, 'size': size})
metadata = sorted(metadata, key=lambda x: (x['name'], x['version'], x['platform'], x['lang'], x['size']))

product_fail = products is None or len(products) == 0 or len(installers) == 0
search_fail = len(metadata) == 0
if product_fail or search_fail:
    if not args.suppress:
        if product_fail or args.platform == 'all':
            print(f'Could not find any installable products on GOG with search term "{search_term}".')
        else:
            s = 'your platform' if args.platform is None else args.platform.capitalize()
            print(f'Could not find any installable products on GOG for {s}.')
            print('Try running again with -pall to search all platforms.')
    sys.exit(1)


def strint(val):
    try:
        return str(int(val))
    except ValueError:
        return '"' + str(val) + '"'


out_headers = [x.upper() for x in metadata[0].keys()]
if args.output == 'csv':
    print(','.join(out_headers))
    for row in metadata:
        print(','.join([strint(x) for x in row.values()]))
elif args.output == 'json':
    print(json.dumps({'products': metadata}))
elif args.output == 'pipe':
    print('|'.join(out_headers))
    for product in metadata:
        print('|'.join([str(x).replace('|', '\\|') for x in product.values()]))
elif args.output == 'xml':
    print('<?xml version="1.0" encoding="UTF-8"?>')
    print('<products>')
    for product in metadata:
        print('  <product>')
        for key in product.keys():
            print(f'    <{key}>{xml.sax.saxutils.escape(str(product[key]))}</{key}>')
        print('  </product>')
    print('</products>')
else:
    # table output (default)
    print(tabulate.tabulate([x.values() for x in metadata], headers=out_headers))
