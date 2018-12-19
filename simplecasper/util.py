#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Utility functions including those for writing to csv and json files
    and doing simple HTTP requests using the requests library

    classes:
        SimpleHTTPJSON
        SWVersions

    functions:
        to_file

Copyright 2017, <copyright@mzpqnxow.com>
See COPYRIGHT for details
"""
from __future__ import unicode_literals
from __future__ import print_function

from collections import defaultdict
from csv import (
    DictWriter as CSVDictWriter,
    writer as CSVWriter)
from json import dump as json_dump, load as json_load
from os.path import join, dirname, realpath
import warnings


import requests


class SimpleHTTPJSON(object):
    """
        Convenience base class for shortening HTTP pulls of JSON date
        Very small class as it is meant to be extended
    """
    HTTP_HEADER_ACCEPT_JSON = {
        'Accept': 'application/json, text/javascript, */*; q=0.01'}

    def __init__(self):
        super(SimpleHTTPJSON, self).__init__()
        self._cache_path = join(dirname(realpath(__file__)), '..', 'cache')

    def http_get_json(self,
                      url,
                      fatal_exception=True,
                      accepted_codes=[200],
                      verify=True,
                      auth=None,
                      headers=None,
                      timeout=60,
                      encoding='utf-8'):
        """Simple get_http_json function for doing GET of a JSON file"""

        if auth is None:
            auth = []
        if headers is None:
            headers = {}
        headers.update(self.HTTP_HEADER_ACCEPT_JSON)
        client = requests.session()
        client.encoding = encoding
        warnings.filterwarnings("ignore")
        response = client.get(
            url,
            verify=verify,
            auth=auth,
            headers=headers)
        warnings.filterwarnings("always")
        if response.status_code not in accepted_codes:
            if fatal_exception is True:
                print('FATAL: code == %d' % (response.status_code))
                if response.status_code == 401:
                    print('FATAL: did you provide auth credentials?')
                elif response.status_code == 404:
                    print('FATAL: did you specify the correct URL?')
                raise RuntimeError('bad HTTP status code (%d)' % (
                    response.status_code))
            else:
                return None
        try:
            obj = response.json()
            return obj
        except ValueError as err:
            err = err
            if fatal_exception is True:
                raise
            else:
                return None


class SWVersions(SimpleHTTPJSON):
    """
        Class for programmatically getting the current versions of popular
        software. This is done usually via HTTP requests, either directly to
        the vendor or to some third party service
    """
    CHROME_VERSION_URL = 'https://omahaproxy.appspot.com/all.json?os=%s&channel=%s'
    VERGRABBER_URL = 'http://vergrabber.kingu.pl/vergrabber.json'

    def _cache_load(self, cache_file):
        with open(join(self._cache_path, cache_file), 'rb') as read_stream:
            return json_load(read_stream)

    def latest_chrome(self,
                      operating_system='mac',
                      channel='stable',
                      previous=False,
                      version_only=False):
        """
        Retrieve version information for the newest Chrome stable release for Mac
        If previous is True, return both the current and previous version
        If version_only is True, return a simple string or tuple of strings only, without
        including the release date information.
        """
        chrome_version = defaultdict(dict)
        url = self.CHROME_VERSION_URL % (operating_system, channel)
        response = self.http_get_json(url,
                                      verify=False)
        response = response.pop()
        response = response['versions'].pop()
        if version_only is True:
            if previous is True:
                return response['current_version'], response['previous_version']
            return response['current_version']
        chrome_version['current']['version'] = response['current_version']
        chrome_version['current']['reldate'] = response['current_reldate']
        if previous is True:
            chrome_version['previous']['version'] = response['previous_version']
            chrome_version['previous']['reldate'] = response['previous_reldate']
        return chrome_version

    def get_version(self,
                    client_versions=True,
                    server_versions=True,
                    version_only=False,
                    applications=None):
        """
        Get latest versions of many common software packages. If application is
        specified, get versions only for the applications in the list provided
        """
        all_versions = {}
        filtered_versions = {}
        if not filter(None, (client_versions, server_versions)):
            raise RuntimeError('must request either client data, server data, or both')

        obj = self.http_get_json(self.VERGRABBER_URL,
                                 verify=False)
        if server_versions is True:
            all_versions.update(obj['server'])
        if client_versions is True:
            all_versions.update(obj['client'])

        stripped = defaultdict(dict)
        if version_only is True:
            for product, branches in all_versions.iteritems():
                for branch, version_info in branches.iteritems():
                    stripped[product][branch] = version_info['version']
            all_versions = stripped

        if applications is None:
            return all_versions
        for app in applications:
            filtered_versions[app] = all_versions.get(app, 'N/A')
        return filtered_versions


def to_file(dest, obj, csv_fields=None, uniq=True, filter_blanks=True, silent=False):
    """
    Dump to a file based on extension

    If .json, do a standard dump() to the file
    """
    try:
        write_stream = open(dest, 'wb')
    except OSError as err:
        print(err)
        raise

    if dest.endswith('.json'):
        # Basic JSON dump
        json_dump(obj, write_stream, sort_keys=False)
    elif dest.endswith('.csv'):
        # Write out a plain CSV file, or one with a header if csv_fields is
        # specified
        if isinstance(obj, (set, tuple, list)) is False:
            raise RuntimeError(
                'ERROR: csv files must be generated from a list/tuple/set')
        from json import dumps
        print(dumps(obj, indent=2))
        if len(obj) and isinstance(obj[0], dict):
            csv_fields = obj[0].keys()
        if csv_fields is not None:
            writer = CSVDictWriter(write_stream, fieldnames=csv_fields)
            writer.writeheader()
        else:
            writer = CSVWriter(write_stream)
        for row in obj:
            if obj is None:
                continue
            if csv_fields is not None:
                if isinstance(row, dict):
                    row = {k.encode('utf-8'): v.encode(
                        'utf-8') for k, v in row.iteritems()}
                    # new_row[k.encode('utf-8')] = v.encode('utf-8')
                    writer.writerow(row)
                elif csv_fields is not None:
                    writer.writerow(dict(zip(csv_fields, row)))
                else:
                    raise RuntimeError('unknown type for row')
            else:
                writer.writerow(row)
    elif dest.endswith('.lst'):
        if isinstance(obj, (set, tuple, list)) is False:
            raise RuntimeError('ERROR: raw/.lst dump object must be set/tuple/list')
        if uniq is True:
            obj = set(obj)
        for row in obj:
            if isinstance(obj, (str, unicode)) is False:
                raise RuntimeError(
                    'ERROR: raw/.lst files must be list of strings')
            if filter_blanks is True and row.strip() == '':
                continue
            write_stream.write(row + '\n')
    else:
        # Unknown extension, assume list of strings
        print('WARN: unknown file extension, dumping as list of strings')
        for row in obj:
            if not isinstance(row, str):
                raise RuntimeError(
                    'ERROR: lst files must be list of strings')
            write_stream.write(row.strip() + '\n')
    write_stream.close()
    if silent is False:
        print('--- Object dumped to file %s ...' % (dest))
